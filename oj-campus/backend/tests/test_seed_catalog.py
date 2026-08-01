import hashlib
import importlib
import json
from collections import Counter
from dataclasses import replace

import pytest

from app.seed_catalog.types import (
    LEGACY_TITLES,
    MAX_CASE_BYTES,
    MAX_CASES,
    SeedCase,
    SeedProblem,
    validate_catalog,
    validate_problem,
)


def make_problem() -> SeedProblem:
    return SeedProblem(
        title="Synthetic problem",
        difficulty="easy",
        tags=("arrays", "math"),
        statement="Solve the problem.",
        input_text="Read one integer.",
        output_text="Write one integer.",
        cases=(
            SeedCase("1\n", "1\n", is_sample=True),
            SeedCase("2\n", "2\n"),
            SeedCase("3\n", "3\n"),
            SeedCase("4\n", "4\n"),
        ),
    )


LEGACY_CASES = (
    SeedCase("1 2\n", "3\n", is_sample=True),
    SeedCase("-1 1\n", "0\n"),
)
NEW_TOO_FEW_CASES = (
    SeedCase("1\n", "1\n", is_sample=True),
    SeedCase("2\n", "2\n"),
    SeedCase("3\n", "3\n"),
)


def assert_problem_error(problem: SeedProblem, field: str) -> None:
    with pytest.raises(ValueError, match=field) as error:
        validate_problem(problem)
    assert problem.title in str(error.value)


def test_validate_problem_accepts_new_and_legacy_case_policies():
    validate_problem(make_problem())
    validate_problem(replace(make_problem(), title="两数之和", legacy=True, cases=LEGACY_CASES))


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"title": ""}, "title"),
        ({"difficulty": "expert"}, "difficulty"),
        ({"tags": ()}, "tags"),
        ({"cases": NEW_TOO_FEW_CASES}, "hidden"),
    ],
)
def test_validate_problem_rejects_invalid_metadata(change, message):
    with pytest.raises(ValueError, match=message):
        validate_problem(replace(make_problem(), **change))


def test_validate_catalog_rejects_duplicate_titles_and_wrong_counts():
    problem = make_problem()
    with pytest.raises(ValueError, match="duplicate title"):
        validate_catalog((problem, problem))
    with pytest.raises(ValueError, match="difficulty counts"):
        validate_catalog((problem,), expected_counts={"easy": 2, "medium": 0, "hard": 0})


def test_catalog_has_the_final_exact_difficulty_counts():
    from app.seed_catalog import PROBLEMS

    assert len(PROBLEMS) == 100
    assert Counter(problem.difficulty for problem in PROBLEMS) == {
        "easy": 40,
        "medium": 35,
        "hard": 25,
    }


def test_catalog_import_enforces_the_final_exact_difficulty_counts():
    import app.seed_catalog as catalog
    import app.seed_catalog.hard as hard_catalog

    original_hard_problems = hard_catalog.HARD_PROBLEMS
    try:
        hard_catalog.HARD_PROBLEMS = original_hard_problems[:-1]
        with pytest.raises(ValueError, match="difficulty counts"):
            importlib.reload(catalog)
    finally:
        hard_catalog.HARD_PROBLEMS = original_hard_problems
        importlib.reload(catalog)


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"title": "   "}, "title"),
        ({"statement": "\t\n"}, "statement"),
        ({"input_text": "  "}, "input_text"),
        ({"output_text": "\r\n"}, "output_text"),
        ({"title": "x" * 201}, "title"),
        ({"tags": ("x" * 65,)}, "tags"),
        ({"tags": ("arrays", " Arrays ")}, "tags"),
        ({"tags": (" arrays", "math")}, "tags"),
        ({"tags": ("Arrays", "math")}, "tags"),
        ({"cases": tuple(SeedCase(str(index), str(index), index == 0) for index in range(MAX_CASES + 1))}, "cases"),
        ({"time_limit_ms": 99}, "time_limit_ms"),
        ({"time_limit_ms": 5001}, "time_limit_ms"),
    ],
)
def test_validate_problem_rejects_invalid_field_values(change, field):
    assert_problem_error(replace(make_problem(), **change), field)


@pytest.mark.parametrize("case", [
    SeedCase("x" * (MAX_CASE_BYTES + 1), "ok\n", is_sample=True),
    SeedCase("ok\n", "x" * (MAX_CASE_BYTES + 1), is_sample=True),
])
def test_validate_problem_rejects_oversized_case_text(case):
    assert_problem_error(replace(make_problem(), cases=(case, *make_problem().cases[1:])), "cases")


@pytest.mark.parametrize(
    ("case", "location"),
    [
        (SeedCase("\ud800", "ok\\n", is_sample=True), "input"),
        (SeedCase("ok\\n", "\ud800", is_sample=True), "output"),
    ],
)
def test_validate_problem_names_case_location_for_invalid_utf8(case, location):
    with pytest.raises(ValueError, match=rf"problem 'Synthetic problem': cases case 1 {location}"):
        validate_problem(replace(make_problem(), cases=(case, *make_problem().cases[1:])))


def test_validate_problem_rejects_stripped_tags_that_collide_after_casefold():
    assert_problem_error(replace(make_problem(), tags=("é", "É")), "tags")


def test_validate_problem_requires_a_sample_case():
    assert_problem_error(
        replace(make_problem(), cases=tuple(replace(case, is_sample=False) for case in make_problem().cases)),
        "sample",
    )


def test_validate_problem_allows_bfs_only_for_legacy_catalog_entry():
    validate_problem(replace(make_problem(), title="最短路径（无权图）", tags=("图论", "BFS"), legacy=True, cases=LEGACY_CASES))
    assert_problem_error(replace(make_problem(), tags=("BFS", "math")), "tags")


def test_validate_problem_rejects_legacy_flag_for_new_title_case_and_tag_exceptions():
    assert_problem_error(
        replace(make_problem(), legacy=True, cases=LEGACY_CASES),
        "legacy",
    )
    assert_problem_error(
        replace(make_problem(), legacy=True, tags=("Arrays", "math")),
        "legacy",
    )


def test_legacy_titles_are_fixed_original_problem_titles():
    assert LEGACY_TITLES == frozenset({
        "两数之和", "奇偶判断", "区间求和", "最大公约数", "括号匹配", "矩阵行和",
        "最短路径（无权图）", "最长递增子序列长度", "网格最小路径和",
    })


LEGACY_FINGERPRINTS = {
    "两数之和": "17bace538994087fce4ac6bc58f156ccc7873b87d74a9be9a6f4c42bb6d0162b",
    "奇偶判断": "90acfbfd41bb075b05b46c9204024f429cb2f49450c8428dcd59a221b2c09aee",
    "区间求和": "f0f1109c307f4a16e85abe68b6711b610f0e40f08b290cc0eb3585bd1e3aedbb",
    "最大公约数": "8b5ee68cef26fe5ac9e9372a00e00b628d6c613e0fb53511ac721060aa8c0b8b",
    "括号匹配": "feedb4f7d5d52ef248776ff4053ffc67358c10453bc8fdcd264c3805982141e0",
    "矩阵行和": "ac5b27e626356879fe55eb787dab9c71d5694a8f03dbf6d75ac11023cb38a364",
    "最短路径（无权图）": "f530146764dfd369d98678650995294cfd9a1e5f8f3c4ec050c12b17c8aeb112",
    "最长递增子序列长度": "b10c5b71719d5a6fb80a171efa43a0d954de11f45a93257b40b01e5abaf2a041",
    "网格最小路径和": "ed4193366c9e8e065fb6ad733348763a754b229c555377c3179787a797263bdd",
}


def legacy_fingerprint(problem: SeedProblem) -> str:
    payload = {
        "title": problem.title,
        "difficulty": problem.difficulty,
        "time_limit_ms": problem.time_limit_ms,
        "tags": problem.tags,
        "statement": problem.statement,
        "input_text": problem.input_text,
        "output_text": problem.output_text,
        "cases": tuple(
            (case.input_data, case.output_data, case.is_sample)
            for case in problem.cases
        ),
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def test_catalog_preserves_the_original_nine_problems_exactly():
    from app.seed_catalog import PROBLEMS

    assert tuple(problem.title for problem in PROBLEMS[:len(LEGACY_FINGERPRINTS)]) == tuple(LEGACY_FINGERPRINTS)
    legacy_problems = tuple(problem for problem in PROBLEMS if problem.legacy)
    assert tuple(problem.title for problem in legacy_problems) == tuple(LEGACY_FINGERPRINTS)
    assert {
        problem.title: legacy_fingerprint(problem)
        for problem in legacy_problems
    } == LEGACY_FINGERPRINTS
    assert {problem.title: problem.time_limit_ms for problem in legacy_problems} == {
        title: 1000 for title in LEGACY_FINGERPRINTS
    }


def test_legacy_grid_hidden_answer_matches_independently_enumerated_paths():
    from app.seed_catalog.hard import HARD_PROBLEMS

    problem = next(problem for problem in HARD_PROBLEMS if problem.title == "网格最小路径和")
    hidden_case = problem.cases[1]
    values = list(map(int, hidden_case.input_data.split()))
    rows, columns = values[:2]
    grid = [values[2 + row * columns:2 + (row + 1) * columns] for row in range(rows)]
    path_sums: list[int] = []

    def enumerate_paths(row: int, column: int, total: int) -> None:
        total += grid[row][column]
        if row == rows - 1 and column == columns - 1:
            path_sums.append(total)
            return
        if row + 1 < rows:
            enumerate_paths(row + 1, column, total)
        if column + 1 < columns:
            enumerate_paths(row, column + 1, total)

    enumerate_paths(0, 0, 0)

    assert sorted(path_sums) == [5, 6, 8]
    assert hidden_case.output_data == "5\n"


def test_easy_catalog_includes_planned_input_output_titles():
    from app.seed_catalog.easy import EASY_PROBLEMS

    planned_titles = {
        "两数之积",
        "商与余数",
        "长方形周长与面积",
        "秒数转换",
        "整数数位分解",
    }
    assert planned_titles <= {problem.title for problem in EASY_PROBLEMS}


def test_easy_catalog_includes_planned_branch_titles():
    from app.seed_catalog.easy import EASY_PROBLEMS

    planned_titles = {
        "三数最大值",
        "成绩等级",
        "闰年判断",
        "三角形判定",
    }
    assert planned_titles <= {problem.title for problem in EASY_PROBLEMS}


def test_easy_catalog_includes_planned_loop_math_titles():
    from app.seed_catalog.easy import EASY_PROBLEMS

    planned_titles = {
        "阶乘",
        "质数判断",
        "约数个数",
        "数字反转",
        "完全数判断",
        "斐波那契第 N 项",
    }
    assert planned_titles <= {problem.title for problem in EASY_PROBLEMS}


def test_easy_catalog_includes_planned_array_titles():
    from app.seed_catalog.easy import EASY_PROBLEMS

    planned_titles = {
        "数组最大值",
        "数组逆序",
        "统计正负零",
        "删除指定元素",
        "数组循环右移",
        "第二大不同值",
        "有序数组合并",
        "矩阵转置",
    }
    assert planned_titles <= {problem.title for problem in EASY_PROBLEMS}


def test_easy_catalog_includes_planned_string_titles():
    from app.seed_catalog.easy import EASY_PROBLEMS

    planned_titles = {
        "字符串长度统计",
        "回文字符串",
        "字母频次",
        "大小写转换",
        "单词计数",
        "删除连续重复字符",
        "字符串循环左移",
    }
    assert planned_titles <= {problem.title for problem in EASY_PROBLEMS}


def test_easy_catalog_includes_planned_simulation_titles_and_exact_count():
    from app.seed_catalog.easy import EASY_PROBLEMS

    planned_titles = {
        "数字各位之和",
        "日期的下一天",
        "时钟增加分钟",
        "简易计算器",
        "三的倍数报数",
        "自动售货机找零",
        "电梯运行时间",
    }
    titles = [problem.title for problem in EASY_PROBLEMS]

    assert planned_titles <= set(titles)
    assert len(EASY_PROBLEMS) == 40
    assert all(problem.difficulty == "easy" for problem in EASY_PROBLEMS)
    assert len(titles) == len(set(titles))


def test_easy_catalog_contains_reviewed_boundary_cases():
    from app.seed_catalog.easy import EASY_PROBLEMS

    problems = {problem.title: problem for problem in EASY_PROBLEMS}
    expected_cases = {
        "秒数转换": (
            SeedCase("60\n", "0 1 0\n"),
            SeedCase("3600\n", "1 0 0\n"),
        ),
        "成绩等级": (
            SeedCase("90\n", "A\n"),
            SeedCase("80\n", "B\n"),
        ),
        "质数判断": (SeedCase("999999937\n", "Yes\n"),),
        "单词计数": (SeedCase("     \n", "0\n"),),
    }

    for title, cases in expected_cases.items():
        for case in cases:
            assert case in problems[title].cases


def test_medium_catalog_includes_planned_sorting_titles():
    from app.seed_catalog.medium import MEDIUM_PROBLEMS

    planned_titles = {
        "成绩稳定排序",
        "二分查找首次出现",
        "木材切割",
        "最小可行速度",
        "第 K 小元素",
    }
    assert planned_titles <= {problem.title for problem in MEDIUM_PROBLEMS}


def test_medium_catalog_includes_planned_sequence_titles():
    from app.seed_catalog.medium import MEDIUM_PROBLEMS

    planned_titles = {
        "区间和查询",
        "差分区间增量",
        "和为 K 的连续子数组",
        "最长不重复子串",
        "盛水最多的容器",
    }
    assert planned_titles <= {problem.title for problem in MEDIUM_PROBLEMS}


def test_medium_catalog_includes_planned_container_titles():
    from app.seed_catalog.medium import MEDIUM_PROBLEMS

    planned_titles = {
        "后缀表达式求值",
        "下一个更大元素",
        "滑动窗口最大值",
        "词频最高的单词",
        "循环队列模拟",
    }
    assert planned_titles <= {problem.title for problem in MEDIUM_PROBLEMS}


def test_medium_catalog_includes_planned_search_titles():
    from app.seed_catalog.medium import MEDIUM_PROBLEMS

    planned_titles = {
        "迷宫最短路",
        "岛屿数量",
        "全排列",
        "子集和判定",
        "骑士最短路",
        "最大连通块",
    }
    assert planned_titles <= {problem.title for problem in MEDIUM_PROBLEMS}


def test_medium_catalog_includes_planned_greedy_titles():
    from app.seed_catalog.medium import MEDIUM_PROBLEMS

    planned_titles = {
        "活动选择",
        "最少区间覆盖",
        "删除 K 位数字",
        "最少会议室",
        "加油站环行",
    }
    assert planned_titles <= {problem.title for problem in MEDIUM_PROBLEMS}


def test_medium_catalog_includes_planned_dp_titles_and_exact_count():
    from app.seed_catalog.medium import MEDIUM_PROBLEMS

    planned_titles = {
        "爬楼梯",
        "最大子段和",
        "零一背包",
        "最长公共子序列",
        "数字三角形",
        "最少硬币数量",
    }
    titles = [problem.title for problem in MEDIUM_PROBLEMS]

    assert planned_titles <= set(titles)
    assert len(MEDIUM_PROBLEMS) == 35
    assert all(problem.difficulty == "medium" for problem in MEDIUM_PROBLEMS)
    assert len(titles) == len(set(titles))


def test_hard_catalog_includes_planned_graph_titles():
    from app.seed_catalog.hard import HARD_PROBLEMS

    planned_titles = {
        "Dijkstra 最短路",
        "拓扑排序",
        "最小生成树",
        "二分图判定",
        "树的直径",
        "网络延迟",
    }
    assert planned_titles <= {problem.title for problem in HARD_PROBLEMS}


def test_hard_catalog_includes_planned_dynamic_programming_titles():
    from app.seed_catalog.hard import HARD_PROBLEMS

    planned_titles = {
        "编辑距离",
        "石子合并",
        "树上最大独立集",
        "子集和方案数",
        "股票交易 K 次",
    }
    assert planned_titles <= {problem.title for problem in HARD_PROBLEMS}


def test_hard_catalog_includes_planned_search_titles():
    from app.seed_catalog.hard import HARD_PROBLEMS

    planned_titles = {
        "N 皇后计数",
        "数独求解",
        "单词搜索路径",
        "双向搜索单词阶梯",
    }
    assert planned_titles <= {problem.title for problem in HARD_PROBLEMS}


def test_hard_catalog_includes_planned_data_structure_titles():
    from app.seed_catalog.hard import HARD_PROBLEMS

    planned_titles = {
        "并查集连通性",
        "带权并查集关系",
        "合并 K 个有序序列",
        "树状数组区间和",
    }
    assert planned_titles <= {problem.title for problem in HARD_PROBLEMS}


def test_hard_catalog_includes_planned_simulation_titles():
    from app.seed_catalog.hard import HARD_PROBLEMS

    planned_titles = {
        "LRU 缓存模拟",
        "列车时刻冲突",
        "带括号表达式求值",
    }
    titles = [problem.title for problem in HARD_PROBLEMS]

    assert planned_titles <= set(titles)
    assert len(HARD_PROBLEMS) == 25
    assert all(problem.difficulty == "hard" for problem in HARD_PROBLEMS)
    assert len(titles) == len(set(titles))
