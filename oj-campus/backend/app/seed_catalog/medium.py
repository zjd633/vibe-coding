"""Legacy medium seed problems."""
from __future__ import annotations

from .types import SeedCase, SeedProblem


MEDIUM_PROBLEMS: tuple[SeedProblem, ...] = (
    SeedProblem(
        title="最大公约数",
        difficulty="medium",
        tags=("数学", "欧几里得算法"),
        statement="求两个非零整数的最大公约数。",
        input_text="两个整数 a、b。",
        output_text="输出 gcd(|a|,|b|)。",
        cases=(
            SeedCase("18 24\n", "6\n", is_sample=True),
            SeedCase("1071 462\n", "21\n"),
        ),
        legacy=True,
    ),
    SeedProblem(
        title="括号匹配",
        difficulty="medium",
        tags=("栈", "字符串"),
        statement="给定只含 ()[]{} 的字符串，判断括号是否正确匹配。",
        input_text="一行非空字符串。",
        output_text="匹配输出 YES，否则输出 NO。",
        cases=(
            SeedCase("([]{})\n", "YES\n", is_sample=True),
            SeedCase("([)]\n", "NO\n"),
        ),
        legacy=True,
    ),
    SeedProblem(
        title="矩阵行和",
        difficulty="medium",
        tags=("数组", "二维数组"),
        statement="输出 n×m 整数矩阵每一行的和。",
        input_text="第一行 n m，随后 n 行每行 m 个整数。",
        output_text="每行输出一个行和。",
        cases=(
            SeedCase("2 3\n1 2 3\n4 5 6\n", "6\n15\n", is_sample=True),
            SeedCase("1 4\n-1 1 -1 1\n", "0\n"),
        ),
        legacy=True,
    ),
    SeedProblem(
        title="成绩稳定排序",
        difficulty="medium",
        tags=("排序", "稳定排序"),
        statement=(
            "给定 n 名学生的英文姓名与整数成绩。姓名互不相同且不含空格，成绩在 0 到 100 之间。"
            "请按成绩从高到低排序；成绩相同时，必须保持这些学生在输入中的先后顺序。"
            "1≤n≤200000，姓名只含英文字母且长度为 1 到 20。"
        ),
        input_text="第一行输入整数 n。随后 n 行每行输入一个姓名 name 和一个成绩 score，以空格分隔。",
        output_text="按排序结果输出 n 行，每行输出 `name score`，姓名与成绩之间用一个空格分隔。",
        cases=(
            SeedCase(
                "5\nalice 90\nbob 100\ncarol 90\ndave 75\nerin 100\n",
                "bob 100\nerin 100\nalice 90\ncarol 90\ndave 75\n",
                is_sample=True,
            ),
            SeedCase("1\nSolo 0\n", "Solo 0\n"),
            SeedCase(
                "4\nAmy 88\nBob 88\nCici 88\nDan 88\n",
                "Amy 88\nBob 88\nCici 88\nDan 88\n",
            ),
            SeedCase(
                "6\nA 0\nB 100\nC 50\nD 100\nE 0\nF 50\n",
                "B 100\nD 100\nC 50\nF 50\nA 0\nE 0\n",
            ),
        ),
    ),
    SeedProblem(
        title="二分查找首次出现",
        difficulty="medium",
        tags=("二分查找", "数组"),
        statement=(
            "给定一个长度为 n 的非递减整数数组和目标值 x，求 x 第一次出现的位置。"
            "位置从 1 开始编号；如果 x 不在数组中，输出 -1。1≤n≤200000，"
            "数组元素和 x 均在 -10^9 到 10^9 之间。"
        ),
        input_text="第一行输入整数 n。第二行输入 n 个非递减整数。第三行输入目标整数 x。",
        output_text="输出一个整数：x 第一次出现的 1-based 位置；不存在时输出 -1。",
        cases=(
            SeedCase("8\n1 2 2 2 4 5 5 9\n2\n", "2\n", is_sample=True),
            SeedCase("5\n-3 -3 0 7 9\n-3\n", "1\n"),
            SeedCase("6\n1 2 3 4 8 8\n8\n", "5\n"),
            SeedCase("7\n-5 -1 0 0 3 6 10\n2\n", "-1\n"),
        ),
    ),
    SeedProblem(
        title="木材切割",
        difficulty="medium",
        tags=("二分答案", "数学"),
        statement=(
            "有 n 根长度为正整数的木材，要从中切出至少 k 段长度相同的木材，余料可以丢弃。"
            "切出的小段长度必须是正整数，并保证至少存在一种可行方案。求小段长度的最大值。"
            "1≤n≤200000，1≤k≤10^18，1≤每根木材长度≤10^9，且所有木材长度之和不少于 k。"
            "计算可切段数之和时应使用 signed 64 位整数。"
        ),
        input_text="第一行输入整数 n 和整数 k。第二行输入 n 个木材长度，以空格分隔。",
        output_text="输出一个正整数，表示能够切出至少 k 段时的最大整数段长。",
        cases=(
            SeedCase("4 7\n20 15 10 17\n", "7\n", is_sample=True),
            SeedCase("1 1\n1000000000\n", "1000000000\n"),
            SeedCase("3 9\n5 5 5\n", "1\n"),
            SeedCase("2 5\n10 10\n", "3\n"),
        ),
    ),
    SeedProblem(
        title="最小可行速度",
        difficulty="medium",
        tags=("二分答案", "向上取整"),
        statement=(
            "有 n 份正整数工作量，第 i 份为 ai。处理速度为正整数 v 时，第 i 份工作需要 "
            "ceil(ai/v) 个整小时；每个小时只能处理当前选定的一份工作，完成一份后才能处理下一份。"
            "给定总时限 h，求使全部工作耗时之和不超过 h 的最小速度 v。"
            "1≤n≤200000，n≤h≤10^18，1≤ai≤10^9。累加总耗时时应使用 signed 64 位整数。"
        ),
        input_text="第一行输入整数 n 和整数 h。第二行输入 n 个工作量 ai，以空格分隔。",
        output_text="输出一个正整数，表示满足总耗时不超过 h 的最小速度。",
        cases=(
            SeedCase("4 8\n3 6 7 11\n", "4\n", is_sample=True),
            SeedCase("4 4\n1 10 3 5\n", "10\n"),
            SeedCase("3 100\n1 2 100\n", "2\n"),
            SeedCase("1 3\n8\n", "3\n"),
        ),
    ),
    SeedProblem(
        title="第 K 小元素",
        difficulty="medium",
        tags=("排序", "选择"),
        statement=(
            "给定一个未排序的长度为 n 的整数数组，求其中第 k 小的元素。k 从 1 开始计数，"
            "重复值按它们在数组中的出现次数分别参与排名。1≤n≤200000，1≤k≤n，"
            "每个数组元素在 -10^9 到 10^9 之间。"
        ),
        input_text="第一行输入整数 n 和整数 k。第二行输入 n 个整数，以空格分隔。",
        output_text="输出一个整数，表示数组中第 k 小的元素。",
        cases=(
            SeedCase("7 4\n7 2 5 2 9 1 5\n", "5\n", is_sample=True),
            SeedCase("5 1\n0 -10 8 -10 3\n", "-10\n"),
            SeedCase("6 6\n4 4 2 9 1 9\n", "9\n"),
            SeedCase("8 5\n3 3 3 1 2 2 4 5\n", "3\n"),
        ),
    ),
    SeedProblem(
        title="区间和查询",
        difficulty="medium",
        tags=("前缀和", "数组"),
        statement=(
            "给定一个长度为 n 的整数数组和 q 次查询。每次查询给出闭区间 [l,r]，"
            "下标从 1 开始，求该区间内所有元素之和。1≤n,q≤200000，"
            "-10^9≤ai≤10^9，1≤l≤r≤n；区间和保证在 signed 64 位整数范围内。"
        ),
        input_text=(
            "第一行输入整数 n 和 q。第二行输入 n 个整数 ai。随后 q 行，每行输入两个整数 l r，"
            "表示一次 inclusive、1-based 的区间查询。"
        ),
        output_text="按查询顺序输出 q 行，每行输出对应区间的一个 64 位整数和。",
        cases=(
            SeedCase(
                "5 4\n2 -1 3 5 -2\n1 3\n2 5\n4 4\n1 5\n",
                "4\n5\n5\n7\n",
                is_sample=True,
            ),
            SeedCase(
                "1 3\n-1000000000\n1 1\n1 1\n1 1\n",
                "-1000000000\n-1000000000\n-1000000000\n",
            ),
            SeedCase(
                "4 2\n1000000000 1000000000 1000000000 1000000000\n1 4\n2 3\n",
                "4000000000\n2000000000\n",
            ),
            SeedCase("6 3\n-5 8 -2 7 -10 4\n2 4\n3 6\n5 6\n", "13\n-1\n-6\n"),
        ),
    ),
    SeedProblem(
        title="差分区间增量",
        difficulty="medium",
        tags=("差分", "数组"),
        statement=(
            "给定一个长度为 n 的整数数组，执行 m 次区间增量操作。每次把闭区间 [l,r] 内的"
            "每个元素都加上整数 d，下标从 1 开始。所有操作完成后输出最终数组。"
            "1≤n≤200000，0≤m≤200000，-10^9≤初始元素,d≤10^9，1≤l≤r≤n；"
            "每个最终元素保证在 signed 64 位整数范围内。"
        ),
        input_text=(
            "第一行输入整数 n 和 m。第二行输入 n 个初始元素。随后 m 行每行输入 l r d，"
            "表示对 inclusive、1-based 区间 [l,r] 加 d。m=0 时没有后续操作行。"
        ),
        output_text="输出一行 n 个 64 位整数，表示最终数组，相邻整数用一个空格分隔。",
        cases=(
            SeedCase(
                "5 3\n1 2 3 4 5\n1 3 2\n2 5 -1\n4 4 10\n",
                "3 3 4 13 4\n",
                is_sample=True,
            ),
            SeedCase("1 3\n0\n1 1 5\n1 1 -2\n1 1 10\n", "13\n"),
            SeedCase("4 2\n1 1 1 1\n1 4 -1\n2 3 5\n", "0 5 5 0\n"),
            SeedCase("5 0\n-2 0 7 -9 4\n", "-2 0 7 -9 4\n"),
        ),
    ),
    SeedProblem(
        title="和为 K 的连续子数组",
        difficulty="medium",
        tags=("双指针", "滑动窗口"),
        statement=(
            "给定一个长度为 n、所有元素均为正整数的数组和正整数 K，统计元素和恰好等于 K 的"
            "非空连续子数组数量。只输出数量，不输出区间、下标或长度。1≤n≤200000，"
            "1≤ai≤10^9，1≤K≤10^18；窗口和与答案均应使用 signed 64 位整数。"
        ),
        input_text="第一行输入整数 n 和 K。第二行输入 n 个正整数 ai，以空格分隔。",
        output_text="输出一个 64 位整数，表示和恰好为 K 的非空连续子数组数量。",
        cases=(
            SeedCase("5 5\n1 2 3 2 5\n", "3\n", is_sample=True),
            SeedCase("4 100\n1 2 3 4\n", "0\n"),
            SeedCase("5 2\n1 1 1 1 1\n", "4\n"),
            SeedCase("1 7\n7\n", "1\n"),
        ),
    ),
    SeedProblem(
        title="最长不重复子串",
        difficulty="medium",
        tags=("字符串", "滑动窗口"),
        statement=(
            "给定一个非空字符串 s，求不含重复字符的最长连续子串长度。字符串只含 ASCII 英文字母"
            "和数字，不含空格，并且区分大小写。1≤|s|≤200000。"
        ),
        input_text="输入一行非空字符串 s，行末换行不属于字符串内容。",
        output_text="输出一个整数，表示最长无重复字符连续子串的长度。",
        cases=(
            SeedCase("abcabcbb\n", "3\n", is_sample=True),
            SeedCase("aaaaa\n", "1\n"),
            SeedCase("pwwkew\n", "3\n"),
            SeedCase("aA1aA2\n", "4\n"),
        ),
    ),
    SeedProblem(
        title="盛水最多的容器",
        difficulty="medium",
        tags=("双指针", "数组"),
        statement=(
            "有 n 条竖线，第 i 条位于 1-based 位置 i，高度为非负整数 hi。选择 i<j 两条线时，"
            "它们与底边构成的容器容量为 (j-i)×min(hi,hj)。求所有选择中的最大容量。"
            "2≤n≤200000，0≤hi≤10^9；容量保证在 signed 64 位整数范围内。"
        ),
        input_text="第一行输入整数 n。第二行输入 n 个非负整数高度 hi，以空格分隔。",
        output_text="输出一个 64 位整数，表示最大容量。",
        cases=(
            SeedCase("9\n1 8 6 2 5 4 8 3 7\n", "49\n", is_sample=True),
            SeedCase("4\n0 0 0 0\n", "0\n"),
            SeedCase("5\n1 2 3 4 5\n", "6\n"),
            SeedCase("2\n1000000000 1000000000\n", "1000000000\n"),
        ),
    ),
    SeedProblem(
        title="后缀表达式求值",
        difficulty="medium",
        tags=("栈", "表达式"),
        statement=(
            "给定一个有效的后缀表达式。每个 token 是 signed 64 位整数操作数或运算符 +、-、*、/。"
            "遇到运算符时，先弹出的数是右操作数，后弹出的数是左操作数。保证除数不为 0，"
            "每次除法都能整除，并保证所有中间结果和最终结果都在 signed 64 位整数范围内。"
            "1≤token 数≤200000，表达式最终恰好得到一个结果。"
        ),
        input_text="第一行输入整数 t，表示 token 数。第二行输入恰好 t 个以空格分隔的 token。",
        output_text="输出一个 signed 64 位整数，表示后缀表达式的值。",
        cases=(
            SeedCase("7\n2 3 + 4 * 5 -\n", "15\n", is_sample=True),
            SeedCase("5\n-3 -4 * 2 +\n", "14\n"),
            SeedCase("9\n8 2 / 3 5 * + 7 -\n", "12\n"),
            SeedCase("5\n20 -5 / 6 +\n", "2\n"),
        ),
    ),
    SeedProblem(
        title="下一个更大元素",
        difficulty="medium",
        tags=("单调栈", "数组"),
        statement=(
            "给定一个长度为 n 的整数数组。对每个元素，寻找它右侧第一个严格大于它的元素，"
            "并输出该元素的值；如果右侧不存在严格更大的元素，输出 -1。相等元素不算更大。"
            "1≤n≤200000，-10^9≤ai≤10^9。"
        ),
        input_text="第一行输入整数 n。第二行输入 n 个整数 ai，以空格分隔。",
        output_text="输出一行 n 个整数，依次表示每个位置的下一个严格更大元素值，相邻整数用一个空格分隔。",
        cases=(
            SeedCase("5\n2 1 2 4 3\n", "4 2 4 -1 -1\n", is_sample=True),
            SeedCase("3\n5 5 5\n", "-1 -1 -1\n"),
            SeedCase("5\n5 4 3 2 1\n", "-1 -1 -1 -1 -1\n"),
            SeedCase("1\n-7\n", "-1\n"),
        ),
    ),
    SeedProblem(
        title="滑动窗口最大值",
        difficulty="medium",
        tags=("单调队列", "滑动窗口"),
        statement=(
            "给定一个长度为 n 的整数数组和窗口长度 k。窗口从数组第 1 个元素开始，"
            "每次向右移动一个位置，求每个连续窗口中的最大值。1≤n≤200000，1≤k≤n，"
            "-10^9≤ai≤10^9。"
        ),
        input_text="第一行输入整数 n 和 k。第二行输入 n 个整数 ai，以空格分隔。",
        output_text="按窗口起点顺序输出一行 n-k+1 个最大值，相邻整数用一个空格分隔。",
        cases=(
            SeedCase("8 3\n1 3 -1 -3 5 3 6 7\n", "3 3 5 5 6 7\n", is_sample=True),
            SeedCase("5 1\n4 -2 7 7 0\n", "4 -2 7 7 0\n"),
            SeedCase("4 4\n-5 2 9 1\n", "9\n"),
            SeedCase("4 2\n-1 -3 -3 -2\n", "-1 -3 -2\n"),
        ),
    ),
    SeedProblem(
        title="词频最高的单词",
        difficulty="medium",
        tags=("哈希表", "字符串"),
        statement=(
            "给定 n 个只含小写英文字母的非空单词，统计出现次数最高的单词。"
            "如果多个单词并列最高频，输出普通小写英文字典序最小者：从左到右比较，"
            "首个不同字符较小的单词更小；若一个单词是另一个的前缀，则较短者更小。"
            "1≤n≤200000，每个单词长度为 1 到 30。"
        ),
        input_text="第一行输入整数 n。随后输入 n 个以空白分隔的小写英文单词，可分布在一行或多行。",
        output_text="输出一行 `word count`，单词与它的出现次数之间用一个空格分隔。",
        cases=(
            SeedCase(
                "7\napple banana apple pear banana apple pear\n",
                "apple 3\n",
                is_sample=True,
            ),
            SeedCase("6\ncat dog ant dog cat ant\n", "ant 2\n"),
            SeedCase("4\na aa aa a\n", "a 2\n"),
            SeedCase("1\nzebra\n", "zebra 1\n"),
        ),
    ),
    SeedProblem(
        title="循环队列模拟",
        difficulty="medium",
        tags=("队列", "模拟"),
        statement=(
            "模拟一个初始为空、固定容量为 c 的先进先出循环队列，共执行 q 条操作。"
            "`PUSH x`：未满时把 x 加到队尾并输出 OK；已满时输出 FULL，且队列不变。"
            "`POP`：为空时输出 EMPTY；否则输出并删除队首元素。"
            "`FRONT`：为空时输出 EMPTY；否则只输出队首元素而不删除。"
            "1≤c,q≤200000，-10^9≤x≤10^9。每条操作都必须产生恰好一行输出。"
        ),
        input_text="第一行输入容量 c 和操作数 q。随后 q 行每行是一条 `PUSH x`、`POP` 或 `FRONT` 操作。",
        output_text="按操作顺序输出 q 行，内容遵循题面中的 OK、FULL、EMPTY 或队列元素值规则。",
        cases=(
            SeedCase(
                "3 11\nPUSH 10\nPUSH 20\nPUSH 30\nPOP\nPUSH 40\nFRONT\nPUSH 50\nPOP\nPOP\nPOP\nPOP\n",
                "OK\nOK\nOK\n10\nOK\n20\nFULL\n20\n30\n40\nEMPTY\n",
                is_sample=True,
            ),
            SeedCase(
                "1 6\nFRONT\nPUSH -5\nFRONT\nPUSH 6\nPOP\nPOP\n",
                "EMPTY\nOK\n-5\nFULL\n-5\nEMPTY\n",
            ),
            SeedCase(
                "2 5\nPUSH 7\nFRONT\nFRONT\nPOP\nFRONT\n",
                "OK\n7\n7\n7\nEMPTY\n",
            ),
            SeedCase(
                "2 8\nPUSH 1\nPUSH 2\nPOP\nPUSH 3\nPOP\nPUSH 4\nFRONT\nPOP\n",
                "OK\nOK\n1\nOK\n2\nOK\n3\n3\n",
            ),
        ),
    ),
    SeedProblem(
        title="迷宫最短路",
        difficulty="medium",
        tags=("搜索", "bfs"),
        statement=(
            "给定一个 n 行 m 列的字符迷宫，字符 `0` 表示可以进入的格子，字符 `1` 表示墙。"
            "再给出起点 (sx,sy) 和终点 (tx,ty)，坐标均从 1 开始，且起点、终点保证为 `0`。"
            "每一步只能向上、下、左、右移动到相邻的可走格，求从起点到终点的最少步数；"
            "若无法到达则输出 -1。1≤n,m≤1000，且 n×m≤10^6。"
        ),
        input_text=(
            "第一行输入整数 n 和 m。随后 n 行各输入一个长度为 m、只含 0 和 1 的字符串。"
            "最后一行输入 sx sy tx ty，表示 1-based 起点和终点坐标。"
        ),
        output_text="输出一个整数，表示四方向移动的最少步数；不可达时输出 -1。",
        cases=(
            SeedCase("3 4\n0000\n0110\n0000\n1 1 3 4\n", "5\n", is_sample=True),
            SeedCase("1 1\n0\n1 1 1 1\n", "0\n"),
            SeedCase("2 2\n01\n10\n1 1 2 2\n", "-1\n"),
            SeedCase("4 4\n0001\n1100\n0000\n0110\n1 1 4 4\n", "6\n"),
        ),
    ),
    SeedProblem(
        title="岛屿数量",
        difficulty="medium",
        tags=("搜索", "dfs"),
        statement=(
            "给定一个 n 行 m 列的字符网格，`1` 表示陆地，`0` 表示水域。"
            "上下或左右相邻的陆地格属于同一座岛屿，对角相邻不连通。"
            "求网格中的岛屿数量。1≤n,m≤1000，且 n×m≤10^6。"
        ),
        input_text="第一行输入整数 n 和 m；随后 n 行各输入一个长度为 m、只含 0 和 1 的字符串。",
        output_text="输出一个非负整数，表示按四方向连通得到的岛屿数量。",
        cases=(
            SeedCase("4 5\n11000\n11010\n00010\n10101\n", "5\n", is_sample=True),
            SeedCase("2 3\n000\n000\n", "0\n"),
            SeedCase("3 3\n111\n111\n111\n", "1\n"),
            SeedCase("3 4\n1001\n1100\n0011\n", "3\n"),
        ),
    ),
    SeedProblem(
        title="全排列",
        difficulty="medium",
        tags=("回溯", "枚举"),
        statement=(
            "给定整数 n，输出数字 1 到 n 的所有排列。排列之间必须按字典序从小到大输出："
            "先比较第一个不同位置，该位置数字较小的排列排在前面。1≤n≤8。"
            "输出恰好 n! 行，不得输出标题、序号或多余空行。"
        ),
        input_text="输入一行一个整数 n。",
        output_text="按严格字典序输出 n! 行；每行包含 n 个整数，相邻整数之间用一个空格分隔。",
        cases=(
            SeedCase(
                "3\n",
                "1 2 3\n1 3 2\n2 1 3\n2 3 1\n3 1 2\n3 2 1\n",
                is_sample=True,
            ),
            SeedCase("1\n", "1\n"),
            SeedCase("2\n", "1 2\n2 1\n"),
            SeedCase(
                "4\n",
                "1 2 3 4\n1 2 4 3\n1 3 2 4\n1 3 4 2\n1 4 2 3\n1 4 3 2\n"
                "2 1 3 4\n2 1 4 3\n2 3 1 4\n2 3 4 1\n2 4 1 3\n2 4 3 1\n"
                "3 1 2 4\n3 1 4 2\n3 2 1 4\n3 2 4 1\n3 4 1 2\n3 4 2 1\n"
                "4 1 2 3\n4 1 3 2\n4 2 1 3\n4 2 3 1\n4 3 1 2\n4 3 2 1\n",
            ),
        ),
    ),
    SeedProblem(
        title="子集和判定",
        difficulty="medium",
        tags=("搜索", "动态规划"),
        statement=(
            "给定 n 个非负整数和非负目标值 S，判断能否从中选出若干个数，使它们的和恰好为 S。"
            "每个输入位置至多选择一次，即使数值相同也视为不同位置；允许选择空集，所以 S=0 时答案为 Yes。"
            "1≤n≤40，0≤ai≤10^12，0≤S≤10^12，所有被选数之和保证在 signed 64 位整数范围内。"
        ),
        input_text="第一行输入整数 n 和目标值 S；第二行输入 n 个非负整数 ai。",
        output_text="存在满足条件的子集时输出 `Yes`，否则输出 `No`，大小写必须完全一致。",
        cases=(
            SeedCase("5 9\n3 34 4 12 5\n", "Yes\n", is_sample=True),
            SeedCase("3 0\n5 7 9\n", "Yes\n"),
            SeedCase("4 6\n3 3 3 8\n", "Yes\n"),
            SeedCase("5 11\n2 4 6 8 10\n", "No\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="骑士最短路",
        difficulty="medium",
        tags=("搜索", "bfs"),
        statement=(
            "在一个 r 行 c 列、没有障碍的棋盘上，给出骑士的起点和终点。行、列坐标均从 1 开始。"
            "骑士每步可按八种标准方式移动，即坐标变化为 (±1,±2) 或 (±2,±1)，且不能移出棋盘。"
            "求到达终点的最少步数；无法到达时输出 -1。1≤r,c≤1000，且 r×c≤10^6。"
        ),
        input_text="输入一行六个整数 r c sx sy tx ty，依次表示棋盘大小和 1-based 起终格坐标。",
        output_text="输出一个整数，表示最少骑士步数；不可达时输出 -1。",
        cases=(
            SeedCase("8 8 1 1 8 8\n", "6\n", is_sample=True),
            SeedCase("1 1 1 1 1 1\n", "0\n"),
            SeedCase("2 3 1 1 2 3\n", "1\n"),
            SeedCase("3 3 1 1 3 3\n", "4\n"),
        ),
    ),
    SeedProblem(
        title="最大连通块",
        difficulty="medium",
        tags=("搜索", "网格"),
        statement=(
            "给定一个 n 行 m 列的字符网格，`1` 表示陆地，`0` 表示水域。"
            "上下或左右相邻的陆地格属于同一个连通块，对角相邻不连通。"
            "求格子数最多的陆地连通块大小；若全是水域则输出 0。1≤n,m≤1000，且 n×m≤10^6。"
        ),
        input_text="第一行输入整数 n 和 m；随后 n 行各输入一个长度为 m、只含 0 和 1 的字符串。",
        output_text="输出一个非负整数，表示四方向陆地连通块的最大格子数。",
        cases=(
            SeedCase("4 5\n11000\n11100\n00101\n00111\n", "10\n", is_sample=True),
            SeedCase("2 4\n0000\n0000\n", "0\n"),
            SeedCase("2 3\n111\n111\n", "6\n"),
            SeedCase("3 3\n101\n000\n101\n", "1\n"),
        ),
    ),
    SeedProblem(
        title="活动选择",
        difficulty="medium",
        tags=("贪心", "区间"),
        statement=(
            "有 n 个活动，第 i 个活动占用半开时间区间 [start_i,end_i)，其中 start_i<end_i。"
            "同一时刻最多参加一个活动；若一个活动的结束时刻等于另一个活动的开始时刻，二者不冲突。"
            "求最多能完整参加多少个活动。1≤n≤200000，-10^9≤start_i<end_i≤10^9。"
        ),
        input_text="第一行输入整数 n；随后 n 行每行输入两个整数 start_i end_i，表示半开区间。",
        output_text="输出一个整数，表示两两不冲突的活动最多数量。",
        cases=(
            SeedCase("6\n1 3\n2 5\n4 7\n1 8\n5 9\n8 10\n", "3\n", is_sample=True),
            SeedCase("4\n0 1\n1 2\n2 3\n3 4\n", "4\n"),
            SeedCase("3\n1 4\n1 2\n1 3\n", "1\n"),
            SeedCase("5\n0 10\n1 2\n2 3\n3 4\n4 5\n", "4\n"),
        ),
    ),
    SeedProblem(
        title="最少区间覆盖",
        difficulty="medium",
        tags=("贪心", "区间"),
        statement=(
            "给定目标闭区间 [L,R]（L<R）以及 n 个闭区间 [l_i,r_i]（l_i<r_i）。"
            "选择尽量少的给定区间，使它们的并集覆盖连续实数区间 [L,R] 中的每一点。"
            "闭区间在同一端点相接视为无缝，例如 [0,2] 与 [2,5] 可以连续覆盖 [0,5]。"
            "输出所需的最少区间数；无法完整覆盖时输出 -1。1≤n≤200000，"
            "-10^9≤L<R≤10^9，-10^9≤l_i<r_i≤10^9。"
        ),
        input_text="第一行输入 n L R；随后 n 行每行输入 l_i r_i。所有端点虽为整数，覆盖对象是连续实数区间。",
        output_text="输出最少选择的区间数；不存在完整覆盖方案时输出 -1。",
        cases=(
            SeedCase("5 0 10\n-1 3\n2 6\n6 8\n8 12\n4 9\n", "4\n", is_sample=True),
            SeedCase("2 0 5\n0 2\n2 5\n", "2\n"),
            SeedCase("2 0 5\n0 2\n3 5\n", "-1\n"),
            SeedCase("3 0 10\n-5 20\n0 4\n4 10\n", "1\n"),
        ),
    ),
    SeedProblem(
        title="删除 K 位数字",
        difficulty="medium",
        tags=("贪心", "单调栈"),
        statement=(
            "给定一个表示非负整数的十进制字符串 num，除数字 0 本身外，num 不含前导零。"
            "必须删除恰好 k 个数字，且不得改变其余数字的相对顺序，使得到的非负整数最小。"
            "输出时删除结果的所有前导零；若删除后为空或只剩零，则输出 0。"
            "1≤|num|≤200000，0≤k≤|num|，num 只含字符 0 到 9。"
        ),
        input_text="第一行输入十进制字符串 num；第二行输入整数 k。",
        output_text="输出一行规范化后的最小非负整数，不含多余前导零。",
        cases=(
            SeedCase("1432219\n3\n", "1219\n", is_sample=True),
            SeedCase("10\n1\n", "0\n"),
            SeedCase("10200\n1\n", "200\n"),
            SeedCase("12345\n5\n", "0\n"),
        ),
    ),
    SeedProblem(
        title="最少会议室",
        difficulty="medium",
        tags=("贪心", "排序"),
        statement=(
            "有 n 场会议，第 i 场占用半开时间区间 [start_i,end_i)，其中 start_i<end_i。"
            "同一会议室中的会议不能重叠；结束时刻等于下一场开始时刻时，可立即复用该会议室。"
            "求安排全部会议所需的最少会议室数量。1≤n≤200000，"
            "-10^9≤start_i<end_i≤10^9。"
        ),
        input_text="第一行输入整数 n；随后 n 行每行输入两个整数 start_i end_i，表示一场会议的半开区间。",
        output_text="输出一个整数，表示安排全部会议的最少会议室数。",
        cases=(
            SeedCase("4\n0 30\n5 10\n15 20\n20 25\n", "2\n", is_sample=True),
            SeedCase("4\n0 1\n1 2\n2 3\n3 4\n", "1\n"),
            SeedCase("3\n5 8\n5 7\n5 6\n", "3\n"),
            SeedCase("4\n1 10\n2 3\n3 4\n4 5\n", "2\n"),
        ),
    ),
    SeedProblem(
        title="加油站环行",
        difficulty="medium",
        tags=("贪心", "数组"),
        statement=(
            "环形道路上有 n 个加油站，按 1 到 n 编号。第 i 站可加入 gas_i 单位汽油，"
            "从第 i 站驶往下一站需要 cost_i 单位汽油，第 n 站的下一站是第 1 站。"
            "从所选起点以油箱为 0 开始，到站先加油再驶向下一站；油箱容量无限，途中油量不得为负。"
            "输出能够顺时针完成恰好一圈的最小 1-based 起点；不存在时输出 -1。"
            "测试数据保证可行起点至多一个。1≤n≤200000，0≤gas_i,cost_i≤10^9，"
            "总油量与总耗油量均在 signed 64 位整数范围内。"
        ),
        input_text="第一行输入整数 n；第二行输入 n 个 gas_i；第三行输入 n 个 cost_i。",
        output_text="输出可完成一圈的最小 1-based 起点编号；不存在可行起点时输出 -1。",
        cases=(
            SeedCase("5\n1 2 3 4 5\n3 4 5 1 2\n", "4\n", is_sample=True),
            SeedCase("1\n5\n4\n", "1\n"),
            SeedCase("3\n2 3 4\n3 4 5\n", "-1\n"),
            SeedCase("3\n2 0 2\n1 2 1\n", "3\n"),
        ),
    ),
    SeedProblem(
        title="爬楼梯",
        difficulty="medium",
        tags=("动态规划", "递推"),
        statement=(
            "有一段 n 阶楼梯，每次只能向上走 1 阶或 2 阶，求恰好到达第 n 阶的走法数量。"
            "不同的步长顺序视为不同走法，例如先走 1 阶再走 2 阶与先走 2 阶再走 1 阶不同。"
            "1≤n≤90，答案保证在 signed 64 位整数范围内。"
        ),
        input_text="输入一行一个整数 n，表示楼梯阶数。",
        output_text="输出一个 signed 64 位整数，表示恰好到达第 n 阶的走法数量。",
        cases=(
            SeedCase("5\n", "8\n", is_sample=True),
            SeedCase("1\n", "1\n"),
            SeedCase("2\n", "2\n"),
            SeedCase("10\n", "89\n"),
        ),
    ),
    SeedProblem(
        title="最大子段和",
        difficulty="medium",
        tags=("动态规划", "数组"),
        statement=(
            "给定一个长度为 n 的整数数组，选择一个非空连续子数组，使其中元素之和最大。"
            "必须至少选择一个元素，因此数组全为负数时不能用空数组得到 0。"
            "1≤n≤200000，-10^12≤a_i≤10^12，任意连续子数组的和保证在 signed 64 位整数范围内。"
        ),
        input_text="第一行输入整数 n；第二行输入 n 个整数 a_i，以空格分隔。",
        output_text="输出一个 signed 64 位整数，表示非空连续子数组的最大元素和。",
        cases=(
            SeedCase("8\n-2 1 -3 4 -1 2 1 -5\n", "6\n", is_sample=True),
            SeedCase("6\n-8 -3 -6 -2 -5 -4\n", "-2\n"),
            SeedCase("1\n-1000000000000\n", "-1000000000000\n"),
            SeedCase("3\n1000000000 1000000000 -1\n", "2000000000\n"),
        ),
    ),
    SeedProblem(
        title="零一背包",
        difficulty="medium",
        tags=("动态规划", "背包"),
        statement=(
            "有 n 件物品和一个容量为 C 的背包。第 i 件物品重量为正整数 w_i，价值为非负整数 v_i；"
            "每件物品至多选择一次。求总重量不超过 C 时可获得的最大总价值。"
            "1≤n≤2000，0≤C≤200000，1≤w_i≤10^9，0≤v_i≤10^12，且 n×(C+1)≤2×10^7。"
            "所有物品价值之和保证在 signed 64 位整数范围内。"
        ),
        input_text="第一行输入整数 n 和容量 C；随后 n 行每行输入一件物品的 w_i 和 v_i。",
        output_text="输出一个 signed 64 位整数，表示不超过容量且每件至多选一次时的最大总价值。",
        cases=(
            SeedCase("4 7\n1 1\n3 4\n4 5\n5 7\n", "9\n", is_sample=True),
            SeedCase("3 0\n1 10\n2 20\n3 30\n", "0\n"),
            SeedCase("3 2\n3 100\n4 200\n5 300\n", "0\n"),
            SeedCase("2 6\n3 5\n4 6\n", "6\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="最长公共子序列",
        difficulty="medium",
        tags=("动态规划", "字符串"),
        statement=(
            "给定两个非空、只含小写英文字母的字符串 s 和 t，求它们的最长公共子序列长度。"
            "子序列由原字符串删除若干字符后保持剩余字符相对顺序得到，不要求字符在原串中连续。"
            "1≤|s|,|t|≤2000，且 |s|×|t|≤4×10^6。只需输出长度，不需要输出具体子序列。"
        ),
        input_text="第一行输入字符串 s，第二行输入字符串 t；两行均非空且不含空格。",
        output_text="输出一个非负整数，表示 s 与 t 的最长公共子序列长度。",
        cases=(
            SeedCase("abcde\nace\n", "3\n", is_sample=True),
            SeedCase("abc\ndef\n", "0\n"),
            SeedCase("aaaa\naa\n", "2\n"),
            SeedCase("abcbdab\nbdcaba\n", "4\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="数字三角形",
        difficulty="medium",
        tags=("动态规划", "路径"),
        statement=(
            "给定一个有 n 行的数字三角形，第 i 行有 i 个整数。路径从第 1 行顶点开始；"
            "若当前位于第 i 行第 j 个数，下一步只能走到第 i+1 行第 j 个数或第 j+1 个数。"
            "求走到第 n 行时路径上所有数字之和的最大值。数字可以为负数。"
            "1≤n≤1000，-10^12≤每个数≤10^12，任意合法路径和保证在 signed 64 位整数范围内。"
        ),
        input_text="第一行输入整数 n；随后 n 行，第 i 行输入 i 个整数，表示数字三角形。",
        output_text="输出一个 signed 64 位整数，表示从顶点到最后一行的最大路径和。",
        cases=(
            SeedCase("4\n2\n3 4\n6 5 7\n4 1 8 3\n", "21\n", is_sample=True),
            SeedCase("1\n-5\n", "-5\n"),
            SeedCase("3\n-1\n-2 -3\n-4 -5 -6\n", "-7\n"),
            SeedCase("3\n1000000000000\n1000000000000 1\n1000000000000 1 1\n", "3000000000000\n"),
        ),
    ),
    SeedProblem(
        title="最少硬币数量",
        difficulty="medium",
        tags=("动态规划", "背包"),
        statement=(
            "给定 n 种正整数面额的硬币和非负目标金额 amount，每种硬币可以使用无限枚。"
            "求凑出恰好 amount 所需的真正最少硬币枚数；面额不保证满足贪心性质。"
            "无法恰好凑出时输出 -1，amount=0 时输出 0。1≤n≤100，0≤amount≤100000，"
            "1≤coin_i≤10^9。"
        ),
        input_text="第一行输入整数 n 和 amount；第二行输入 n 个正整数面额 coin_i。",
        output_text="输出凑出 amount 的最少硬币枚数；不可达时输出 -1。",
        cases=(
            SeedCase("3 6\n1 3 4\n", "2\n", is_sample=True),
            SeedCase("2 7\n2 4\n", "-1\n"),
            SeedCase("3 0\n2 5 9\n", "0\n"),
            SeedCase("3 10\n1 5 6\n", "2\n"),
        ),
    ),
)
