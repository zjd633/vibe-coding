from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import psutil
from sqlalchemy import select, update

from .database import session_scope
from .models import Problem, Submission, TestCase, utcnow

GPP_PATH = os.environ.get("OJ_GPP_PATH", r"E:\mingw64\bin\g++.exe")
COMPILE_TIMEOUT_SECONDS = 15
STDOUT_LIMIT = 1024 * 1024
STDERR_LIMIT = 16 * 1024
LOGGER = logging.getLogger(__name__)
CREATE_SUSPENDED = 0x00000004
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
WINDOWS_SANDBOX_WARNING = (
    "Windows 子进程执行不是安全沙箱，仅允许运行受信任的本地代码，绝不能对公网开放。"
)


@dataclass(frozen=True)
class JudgeResult:
    status: str
    runtime_ms: int | None
    failed_case: int | None
    details: str = ""


def normalize_output(value: str) -> str:
    lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [line.rstrip() for line in lines]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _bounded(value: bytes, limit: int = STDERR_LIMIT) -> str:
    return value[:limit].decode("utf-8", errors="replace")


class _WindowsJob:
    def __init__(self, kernel32, handle) -> None:
        self._kernel32 = kernel32
        self._handle = handle
        self._lock = threading.Lock()

    def terminate(self) -> None:
        with self._lock:
            if self._handle and not self._kernel32.TerminateJobObject(self._handle, 1):
                import ctypes

                raise OSError(ctypes.get_last_error(), "TerminateJobObject failed")

    def close(self) -> None:
        with self._lock:
            if not self._handle:
                return
            handle = self._handle
            if not self._kernel32.CloseHandle(handle):
                import ctypes

                raise OSError(ctypes.get_last_error(), "CloseHandle(job) failed")
            self._handle = None


def _close_windows_job_with_retry(job: _WindowsJob, on_final_failure=None, attempts: int = 3) -> None:
    last_error = None
    for _attempt in range(attempts):
        try:
            job.close()
            return
        except Exception as error:
            last_error = error
    if on_final_failure is not None:
        try:
            on_final_failure()
        except Exception:
            LOGGER.exception("process-tree cleanup failed after Windows Job close failure")
    if last_error is not None:
        raise last_error


def _create_windows_job(process: psutil.Popen) -> _WindowsJob:
    """Assign a suspended process before it can spawn descendants."""
    import ctypes
    from ctypes import wintypes

    class BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimitInformation),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateJobObject.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
    job = _WindowsJob(kernel32, handle)
    try:
        limits = ExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            handle, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            raise OSError(ctypes.get_last_error(), "SetInformationJobObject failed")
        if not kernel32.AssignProcessToJobObject(handle, wintypes.HANDLE(int(process._handle))):
            raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")
        return job
    except Exception:
        try:
            _close_windows_job_with_retry(job)
        except Exception as cleanup_error:
            LOGGER.error("Windows Job handle cleanup failed after creation/assignment error", exc_info=(
                type(cleanup_error), cleanup_error, cleanup_error.__traceback__,
            ))
        raise


def _record_descendants(process: subprocess.Popen, descendants: dict[int, psutil.Process], lock: threading.Lock) -> None:
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
    except (psutil.Error, ProcessLookupError):
        return
    with lock:
        for child in children:
            descendants[child.pid] = child


def _kill_recorded_processes(process: subprocess.Popen, descendants: dict[int, psutil.Process],
                             lock: threading.Lock, include_parent: bool,
                             job: _WindowsJob | None = None) -> None:
    if include_parent and job is not None:
        job.terminate()
    _record_descendants(process, descendants, lock)
    with lock:
        targets = list(descendants.values())
    if include_parent and process.poll() is None:
        try:
            targets.append(psutil.Process(process.pid))
        except (psutil.Error, ProcessLookupError):
            pass
    unique = {target.pid: target for target in targets}.values()
    alive = []
    for target in unique:
        try:
            if target.is_running():
                target.kill()
                alive.append(target)
        except (psutil.Error, ProcessLookupError):
            pass
    if alive:
        _gone, alive = psutil.wait_procs(alive, timeout=1)
        for target in alive:
            try:
                target.kill()
            except (psutil.Error, ProcessLookupError):
                pass
        if alive:
            psutil.wait_procs(alive, timeout=1)


@dataclass(frozen=True)
class ProcessResult:
    stdout: bytes
    stderr: bytes
    returncode: int | None
    timed_out: bool
    stdout_overflow: bool
    stderr_truncated: bool
    elapsed_ms: int

    @property
    def overflow(self) -> bool:
        """Compatibility alias: only stdout overflow can produce OLE."""
        return self.stdout_overflow


def _run(command: list[str], cwd: Path, timeout_seconds: float, input_data: str | None = None,
         stdout_limit: int | None = None, stderr_limit: int = STDERR_LIMIT,
         terminate_on_stdout_overflow: bool = False) -> ProcessResult:
    started = time.monotonic()
    popen_type = psutil.Popen if os.name == "nt" else subprocess.Popen
    popen_options = {"creationflags": CREATE_SUSPENDED} if os.name == "nt" else {}
    process = popen_type(command, cwd=cwd, stdin=subprocess.PIPE if input_data is not None else None,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, **popen_options)
    job = None
    if os.name == "nt":
        try:
            job = _create_windows_job(process)
        except Exception as error:
            LOGGER.warning(
                "WARNING: Windows Job Object unavailable; using weaker containment with psutil "
                "/ Windows 作业对象不可用，正使用较弱的 psutil 进程约束",
                exc_info=(type(error), error, error.__traceback__),
            )
    output = bytearray()
    errors = bytearray()
    stdout_overflow = threading.Event()
    stderr_truncated = threading.Event()
    io_error: list[Exception] = []
    descendants: dict[int, psutil.Process] = {}
    descendants_lock = threading.Lock()
    stop_monitor = threading.Event()

    def monitor_descendants() -> None:
        while not stop_monitor.is_set():
            _record_descendants(process, descendants, descendants_lock)
            stop_monitor.wait(0.01)

    def collect(pipe, target: bytearray, limit: int | None, truncated: threading.Event,
                terminate_on_overflow: bool = False) -> None:
        try:
            while chunk := os.read(pipe.fileno(), 8192):
                if limit is not None and len(target) + len(chunk) > limit:
                    target.extend(chunk[:max(0, limit - len(target))])
                    first_overflow = not truncated.is_set()
                    truncated.set()
                    if terminate_on_overflow and first_overflow:
                        _kill_recorded_processes(process, descendants, descendants_lock, include_parent=True, job=job)
                elif limit is None or len(target) < limit:
                    target.extend(chunk)
        except Exception as error:
            io_error.append(error)

    def write_input() -> None:
        try:
            if process.stdin is not None:
                process.stdin.write((input_data or "").encode("utf-8"))
                process.stdin.close()
        except BrokenPipeError:
            # A child may legitimately exit or close stdin before consuming all input.
            pass
        except (OSError, ValueError) as error:
            io_error.append(error)

    monitor_thread = threading.Thread(target=monitor_descendants, daemon=True)
    out_thread = threading.Thread(target=collect, args=(process.stdout, output, stdout_limit, stdout_overflow,
                                                        terminate_on_stdout_overflow), daemon=True)
    err_thread = threading.Thread(target=collect, args=(process.stderr, errors, stderr_limit, stderr_truncated), daemon=True)
    input_thread = threading.Thread(target=write_input, daemon=True) if input_data is not None else None
    monitor_started = out_started = err_started = input_started = False
    timed_out = False
    finished = started
    try:
        monitor_thread.start()
        monitor_started = True
        out_thread.start()
        out_started = True
        err_thread.start()
        err_started = True
        if input_thread:
            input_thread.start()
            input_started = True
        if os.name == "nt":
            process.resume()
        try:
            process.wait(timeout=timeout_seconds)
        except (subprocess.TimeoutExpired, psutil.TimeoutExpired):
            timed_out = True
        finished = time.monotonic()
    finally:
        active_exception = sys.exc_info()[0] is not None
        cleanup_errors: list[Exception] = []

        def cleanup(action) -> None:
            try:
                action()
            except Exception as error:
                cleanup_errors.append(error)

        stop_monitor.set()
        if monitor_started:
            cleanup(lambda: monitor_thread.join(timeout=1))
        force_parent = timed_out or stdout_overflow.is_set() or process.poll() is None
        if force_parent:
            cleanup(lambda: _kill_recorded_processes(
                process, descendants, descendants_lock, include_parent=True, job=job
            ))
        if job is not None:
            cleanup(lambda: _close_windows_job_with_retry(
                job,
                on_final_failure=lambda: _kill_recorded_processes(
                    process, descendants, descendants_lock, include_parent=True
                ),
            ))
        # The Job Object closes the race; psutil remains a portable cleanup and wait fallback.
        cleanup(lambda: _kill_recorded_processes(
            process, descendants, descendants_lock, include_parent=process.poll() is None
        ))
        if process.poll() is None:
            cleanup(process.kill)
        if process.poll() is None:
            cleanup(lambda: process.wait(timeout=1))
        if out_started:
            cleanup(lambda: out_thread.join(timeout=1))
        if err_started:
            cleanup(lambda: err_thread.join(timeout=1))
        if input_thread and input_started:
            cleanup(lambda: input_thread.join(timeout=1))
        if cleanup_errors:
            if active_exception:
                error = cleanup_errors[0]
                LOGGER.error("subprocess cleanup failed while handling another error", exc_info=(type(error), error, error.__traceback__))
            else:
                raise cleanup_errors[0]
    if io_error and not stdout_overflow.is_set():
        raise OSError("subprocess I/O failed") from io_error[0]
    return ProcessResult(bytes(output), bytes(errors), process.returncode, timed_out, stdout_overflow.is_set(),
                         stderr_truncated.is_set(), int((finished - started) * 1000))


def _remove_tree(root: Path) -> None:
    for _attempt in range(3):
        try:
            shutil.rmtree(root, ignore_errors=False)
        except OSError:
            time.sleep(0.05)
            continue
        if not root.exists():
            return
        time.sleep(0.05)
    raise OSError(f"temporary judge directory could not be removed: {root}")


def run_submission(source: str, cases: list[tuple[str, str]], time_limit_ms: int, temp_root: Path | None = None,
                   compiler: str | None = None) -> JudgeResult:
    compiler = compiler or GPP_PATH
    root = Path(tempfile.mkdtemp(prefix="oj-", dir=temp_root))
    runtime_ms = 0
    try:
        source_path = root / "source.cpp"
        executable = root / "program.exe"
        source_path.write_text(source, encoding="utf-8")
        try:
            compiled = _run([compiler, "-O2", "-std=c++17", "-pipe", str(source_path), "-o", str(executable)],
                            root, COMPILE_TIMEOUT_SECONDS, stdout_limit=STDERR_LIMIT)
        except OSError:
            return JudgeResult("SE", None, None, "Compiler unavailable / 编译器不可用")
        if compiled.timed_out:
            return JudgeResult("CE", None, None, "Compilation timed out / 编译超时")
        if compiled.returncode != 0:
            details = _bounded(compiled.stderr).replace(str(root), "<judge>").replace(root.as_posix(), "<judge>")
            return JudgeResult("CE", None, None, details or "Compilation failed / 编译失败")
        for ordinal, (input_data, expected) in enumerate(cases, start=1):
            try:
                ran = _run([str(executable)], root, time_limit_ms / 1000, input_data, STDOUT_LIMIT,
                           terminate_on_stdout_overflow=True)
            except OSError:
                return JudgeResult("SE", None, ordinal, "Program execution failed / 程序执行失败")
            runtime_ms += ran.elapsed_ms
            if ran.stdout_overflow:
                return JudgeResult("OLE", runtime_ms, ordinal)
            if ran.timed_out:
                return JudgeResult("TLE", runtime_ms, ordinal)
            if ran.returncode != 0:
                return JudgeResult("RE", runtime_ms, ordinal, f"Runtime error (exit code {ran.returncode})")
            if normalize_output(ran.stdout.decode("utf-8", errors="replace")) != normalize_output(expected):
                return JudgeResult("WA", runtime_ms, ordinal)
        return JudgeResult("AC", runtime_ms, None)
    finally:
        _remove_tree(root)


def recover_stale_judging(database_url: str) -> int:
    """Requeue every orphaned claim when the single demo worker starts.

    This is startup recovery for the first-release single-worker design; it must
    not be invoked while another worker is actively judging submissions.
    """
    with session_scope(database_url) as db:
        result = db.execute(update(Submission).where(Submission.status == "JUDGING").values(
            status="PENDING", judging_started_at=None,
        ))
        db.commit()
        return result.rowcount or 0


def claim_one(database_url: str) -> int | None:
    with session_scope(database_url) as db:
        candidate = db.scalar(select(Submission.id).where(Submission.status == "PENDING").order_by(Submission.id).limit(1))
        if candidate is None:
            return None
        claimed = db.execute(update(Submission).where(Submission.id == candidate, Submission.status == "PENDING").values(status="JUDGING", judging_started_at=utcnow()))
        db.commit()
        return candidate if claimed.rowcount else None


def process_one(database_url: str, compiler: str | None = None, temp_root: Path | None = None) -> int | None:
    submission_id = claim_one(database_url)
    if submission_id is None:
        return None
    try:
        with session_scope(database_url) as db:
            submission = db.get(Submission, submission_id)
            if submission is None:
                return submission_id
            problem = db.get(Problem, submission.problem_id)
            cases = db.scalars(select(TestCase).where(TestCase.problem_id == submission.problem_id)
                               .order_by(TestCase.position)).all()
            if problem is None:
                result = JudgeResult("SE", None, None, "Submission data unavailable / 提交数据不可用")
            else:
                result = run_submission(submission.source, [(case.input_data, case.output_data) for case in cases],
                                        problem.time_limit_ms, temp_root, compiler)
            submission.status, submission.runtime_ms, submission.failed_case = result.status, result.runtime_ms, result.failed_case
            submission.details = result.details[:STDERR_LIMIT] or None
            submission.judging_started_at = None
            db.commit()
    except Exception:
        LOGGER.exception("judge processing failed for submission %s", submission_id)
        with session_scope(database_url) as recovery_db:
            recovery_db.execute(update(Submission).where(Submission.id == submission_id).values(
                status="SE", runtime_ms=None, failed_case=None,
                details="Judge system error / 评测系统错误", judging_started_at=None))
            recovery_db.commit()
    return submission_id


def run_worker(database_url: str, compiler: str | None = None, poll_seconds: float = 1.0,
               temp_root: Path | None = None, stop_event: threading.Event | None = None,
               max_iterations: int | None = None) -> None:
    """Run a resilient worker loop; optional bounds exist only to make one loop testable."""
    LOGGER.warning(WINDOWS_SANDBOX_WARNING)
    recovery_complete = False
    iterations = 0
    while True:
        if stop_event is not None and stop_event.is_set():
            return
        try:
            if not recovery_complete:
                recover_stale_judging(database_url)
                recovery_complete = True
            submission_id = process_one(database_url, compiler, temp_root)
        except Exception:
            LOGGER.exception("judge worker iteration failed")
            submission_id = None
        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            return
        if submission_id is None:
            if stop_event is not None:
                stop_event.wait(poll_seconds)
            else:
                time.sleep(poll_seconds)


def polling_loop(database_url: str, compiler: str | None = None, poll_seconds: float = 1.0) -> None:
    """Backward-compatible entry point for the production worker."""
    run_worker(database_url, compiler, poll_seconds)
