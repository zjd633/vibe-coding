"""Legacy hard seed problems."""
from __future__ import annotations

from .types import SeedCase, SeedProblem


HARD_PROBLEMS: tuple[SeedProblem, ...] = (
    SeedProblem(
        title="最短路径（无权图）",
        difficulty="hard",
        tags=("图论", "BFS"),
        statement="在无权无向图中求 1 到 n 的最短边数，不可达输出 -1。",
        input_text="n m，随后 m 条边 u v。",
        output_text="输出最短边数。",
        cases=(
            SeedCase("4 4\n1 2\n2 4\n1 3\n3 4\n", "2\n", is_sample=True),
            SeedCase("3 1\n1 2\n", "-1\n"),
        ),
        legacy=True,
    ),
    SeedProblem(
        title="最长递增子序列长度",
        difficulty="hard",
        tags=("动态规划", "二分"),
        statement="求整数序列最长严格递增子序列的长度。",
        input_text="第一行 n，第二行 n 个整数。",
        output_text="输出最长长度。",
        cases=(
            SeedCase("5\n1 3 2 4 3\n", "3\n", is_sample=True),
            SeedCase("4\n4 3 2 1\n", "1\n"),
        ),
        legacy=True,
    ),
    SeedProblem(
        title="网格最小路径和",
        difficulty="hard",
        tags=("动态规划", "网格"),
        statement="只能向右或向下走，求左上到右下的最小路径和。",
        input_text="第一行 n m，随后 n 行 m 个非负整数。",
        output_text="输出最小路径和。",
        cases=(
            SeedCase("2 3\n1 3 1\n1 5 1\n", "6\n", is_sample=True),
            SeedCase("3 2\n1 2\n1 1\n4 2\n", "5\n"),
        ),
        legacy=True,
    ),
    SeedProblem(
        title="Dijkstra 最短路",
        difficulty="hard",
        tags=("图论", "dijkstra", "最短路"),
        statement=(
            "给定一个含 n 个顶点、m 条边的有向图，每条边的权值都是非负整数。"
            "顶点编号为 1 到 n，图中可以有平行边。求从起点 s 到终点 t 的最短距离；"
            "若 t 不可达，输出 -1。路径长度及答案均需使用 64 位有符号整数。"
        ),
        input_text=(
            "第一行输入 n 和 m（1 <= n <= 100000，0 <= m <= 200000）。"
            "接下来 m 行每行输入 u、v、w，表示一条从 u 到 v、权值为 w 的有向边"
            "（1 <= u,v <= n，0 <= w <= 1000000000）。最后一行输入 s 和 t"
            "（1 <= s,t <= n）。"
        ),
        output_text="输出 s 到 t 的最短距离；若不可达，输出 -1。",
        cases=(
            SeedCase(
                "4 5\n1 2 2\n1 3 5\n2 3 0\n3 4 4\n2 4 10\n1 4\n",
                "6\n",
                is_sample=True,
            ),
            SeedCase("3 4\n1 2 10\n1 2 3\n2 3 4\n1 3 20\n1 3\n", "7\n"),
            SeedCase("4 2\n1 2 0\n3 4 1\n1 4\n", "-1\n"),
            SeedCase("3 2\n1 2 1000000000\n2 3 1000000000\n1 3\n", "2000000000\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="拓扑排序",
        difficulty="hard",
        tags=("图论", "拓扑排序", "优先队列"),
        statement=(
            "给定一个含 n 个顶点、m 条边的有向图，顶点编号为 1 到 n。"
            "若图是有向无环图，使用 Kahn 算法进行拓扑排序，并在每一步从当前所有入度为 0 的顶点中"
            "选择编号最小者，输出由此唯一确定的序列；若图中存在环，输出 -1。"
            "没有边相连的顶点也必须出现在序列中。"
        ),
        input_text=(
            "第一行输入 n 和 m（1 <= n <= 200000，0 <= m <= 300000）。"
            "接下来 m 行每行输入 u 和 v，表示一条从 u 到 v 的有向边"
            "（1 <= u,v <= n）。"
        ),
        output_text="若存在环，输出 -1；否则在一行中输出 n 个顶点编号，编号之间以单个空格分隔。",
        cases=(
            SeedCase(
                "6 5\n1 4\n2 4\n2 5\n3 5\n4 6\n",
                "1 2 3 4 5 6\n",
                is_sample=True,
            ),
            SeedCase("4 2\n1 4\n2 3\n", "1 2 3 4\n"),
            SeedCase("3 3\n1 2\n2 3\n3 1\n", "-1\n"),
            SeedCase("5 1\n4 5\n", "1 2 3 4 5\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="最小生成树",
        difficulty="hard",
        tags=("图论", "最小生成树", "kruskal"),
        statement=(
            "给定一个含 n 个顶点、m 条边的无向带权图，顶点编号为 1 到 n，图中可以有平行边。"
            "求一棵最小生成树的边权总和；若图不连通，输出 -1。边权可以为负数，"
            "总权值及答案均需使用 64 位有符号整数。n=1 时最小生成树不含边，总权为 0。"
        ),
        input_text=(
            "第一行输入 n 和 m（1 <= n <= 100000，0 <= m <= 200000）。"
            "接下来 m 行每行输入 u、v、w，表示顶点 u 与 v 之间一条权值为 w 的无向边"
            "（1 <= u,v <= n，-1000000000 <= w <= 1000000000）。"
        ),
        output_text="若图连通，输出最小生成树总权值；否则输出 -1。",
        cases=(
            SeedCase(
                "4 5\n1 2 4\n1 3 1\n2 3 2\n2 4 1\n3 4 5\n",
                "4\n",
                is_sample=True,
            ),
            SeedCase("3 3\n1 2 10\n1 2 -3\n2 3 4\n", "1\n"),
            SeedCase("4 2\n1 2 1\n3 4 2\n", "-1\n"),
            SeedCase("1 0\n", "0\n"),
            SeedCase(
                "4 3\n1 2 -1000000000\n2 3 -1000000000\n3 4 -1000000000\n",
                "-3000000000\n",
            ),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="二分图判定",
        difficulty="hard",
        tags=("图论", "二分图", "染色"),
        statement=(
            "给定一个含 n 个顶点、m 条边的无向图，顶点编号为 1 到 n。"
            "判断能否把所有顶点分成两个集合，使每条边的两个端点属于不同集合。"
            "必须检查所有连通分量；孤立点不影响判定，自环的两个端点相同，因此一定输出 No。"
        ),
        input_text=(
            "第一行输入 n 和 m（1 <= n <= 200000，0 <= m <= 300000）。"
            "接下来 m 行每行输入 u 和 v，表示顶点 u 与 v 之间的一条无向边"
            "（1 <= u,v <= n）。"
        ),
        output_text="若整个图是二分图，输出 Yes；否则输出 No。",
        cases=(
            SeedCase("5 3\n1 2\n2 3\n4 5\n", "Yes\n", is_sample=True),
            SeedCase("6 4\n1 2\n4 5\n5 6\n6 4\n", "No\n"),
            SeedCase("3 2\n1 1\n2 3\n", "No\n"),
            SeedCase("7 4\n1 2\n2 3\n4 5\n4 6\n", "Yes\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="树的直径",
        difficulty="hard",
        tags=("图论", "树", "直径"),
        statement=(
            "给定一棵含 n 个顶点的无向正权树，顶点编号为 1 到 n。"
            "树的直径定义为任意两个顶点之间唯一简单路径的最大边权和。"
            "求这一直径；n=1 时没有边，输出 0。路径和及答案均需使用 64 位有符号整数。"
        ),
        input_text=(
            "第一行输入 n（1 <= n <= 200000）。接下来 n-1 行每行输入 u、v、w，"
            "表示顶点 u 与 v 之间一条权值为 w 的无向边"
            "（1 <= u,v <= n，1 <= w <= 1000000000）。输入保证构成一棵树。"
        ),
        output_text="输出树的直径长度。",
        cases=(
            SeedCase("5\n1 2 3\n2 3 4\n2 4 2\n4 5 6\n", "12\n", is_sample=True),
            SeedCase("1\n", "0\n"),
            SeedCase(
                "4\n1 2 1000000000\n2 3 1000000000\n3 4 1000000000\n",
                "3000000000\n",
            ),
            SeedCase("5\n1 2 2\n1 3 7\n1 4 5\n1 5 1\n", "12\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="网络延迟",
        difficulty="hard",
        tags=("图论", "dijkstra", "最短路"),
        statement=(
            "有 n 个网络节点和 m 条有向传输边，节点编号为 1 到 n，每条边的传输时间为正整数。"
            "信号从源节点 k 同时沿各条边传播，一个节点最早收到信号的时间等于 k 到该点的最短距离。"
            "求所有节点都收到信号所需的时间，即这些最短距离的最大值；若至少有一个节点不可达，"
            "输出 -1。图中可以有平行边，距离及答案均需使用 64 位有符号整数。"
        ),
        input_text=(
            "第一行输入 n、m 和 k（1 <= n <= 100000，0 <= m <= 200000，1 <= k <= n）。"
            "接下来 m 行每行输入 u、v、w，表示一条从 u 到 v、传输时间为 w 的有向边"
            "（1 <= u,v <= n，1 <= w <= 1000000000）。"
        ),
        output_text="输出所有节点收到信号所需的时间；若有节点不可达，输出 -1。",
        cases=(
            SeedCase(
                "4 5 1\n1 2 1\n1 3 4\n2 3 2\n2 4 7\n3 4 1\n",
                "4\n",
                is_sample=True,
            ),
            SeedCase("3 4 1\n1 2 9\n1 2 2\n2 3 5\n1 3 20\n", "7\n"),
            SeedCase("4 2 2\n2 1 3\n2 3 4\n", "-1\n"),
            SeedCase("1 0 1\n", "0\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="编辑距离",
        difficulty="hard",
        tags=("动态规划", "字符串", "编辑距离"),
        statement=(
            "给定两个非空的小写英文字母字符串 a 和 b。你可以对 a 执行三种操作："
            "插入一个字符、删除一个字符或把一个字符替换为另一个字符，每次操作的代价均为 1。"
            "求把 a 变成 b 所需的最少操作次数。"
        ),
        input_text=(
            "第一行输入字符串 a，第二行输入字符串 b。两个字符串都只包含小写英文字母，"
            "且长度均在 1 到 2000 之间。"
        ),
        output_text="输出把 a 变成 b 的最少操作次数。",
        cases=(
            SeedCase("kitten\nsitting\n", "3\n", is_sample=True),
            SeedCase("abc\nabc\n", "0\n"),
            SeedCase("a\nb\n", "1\n"),
            SeedCase("abc\nyabd\n", "2\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="石子合并",
        difficulty="hard",
        tags=("动态规划", "区间动态规划", "前缀和"),
        statement=(
            "有 n 堆石子从左到右排成一条直线，第 i 堆有 a_i 颗石子。"
            "每次只能合并当前相邻的两堆，合并代价等于合并后新堆的石子总数。"
            "求把所有石子合成一堆的最小总代价。所有区间和、中间代价及答案均需使用 64 位有符号整数；"
            "n=1 时无需合并，答案为 0。"
        ),
        input_text=(
            "第一行输入 n（1 <= n <= 300）。第二行输入 n 个整数 a_i"
            "（1 <= a_i <= 1000000000），表示各堆石子数。"
        ),
        output_text="输出合成一堆的最小总代价。",
        cases=(
            SeedCase("4\n1 3 5 2\n", "22\n", is_sample=True),
            SeedCase("1\n1000000000\n", "0\n"),
            SeedCase("2\n1000000000 1000000000\n", "2000000000\n"),
            SeedCase("3\n1 1 1\n", "5\n"),
            SeedCase("4\n4 1 1 4\n", "18\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="树上最大独立集",
        difficulty="hard",
        tags=("动态规划", "树形动态规划", "树"),
        statement=(
            "给定一棵以顶点 1 为根的有根树，每个顶点 i 有整数权值 w_i。"
            "请选择若干顶点，使任意父子相邻的两个顶点不能同时被选择，并最大化所选顶点权值之和。"
            "允许一个顶点都不选，因此答案不会小于 0；顶点权值可以为负数。"
            "所有中间和及答案均需使用 64 位有符号整数。"
        ),
        input_text=(
            "第一行输入 n（1 <= n <= 200000）。第二行输入 n 个整数 w_i"
            "（-1000000000 <= w_i <= 1000000000）。接下来 n-1 行每行输入 parent 和 child，"
            "表示一条从父顶点到子顶点的树边（1 <= parent,child <= n）。"
            "输入保证这些边构成以 1 为根的合法树，且每个非根顶点恰有一个父顶点。"
        ),
        output_text="输出满足父子不能同时选择时的最大权值和。",
        cases=(
            SeedCase(
                "5\n5 1 4 3 2\n1 2\n1 3\n2 4\n2 5\n",
                "10\n",
                is_sample=True,
            ),
            SeedCase("3\n-5 -2 -3\n1 2\n1 3\n", "0\n"),
            SeedCase("3\n1000000000 1000000000 1000000000\n1 2\n1 3\n", "2000000000\n"),
            SeedCase("4\n4 10 -2 8\n1 2\n2 3\n3 4\n", "18\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="子集和方案数",
        difficulty="hard",
        tags=("动态规划", "背包", "计数"),
        statement=(
            "给定 n 个非负整数 a_1 到 a_n 和目标和 S。每个位置的数最多选择一次，"
            "即使两个位置的数值相同，它们也视为不同选择。求所选元素之和恰好为 S 的子集数量。"
            "空集的和为 0；数值为 0 的元素选择或不选择会形成不同子集。答案保证在 64 位有符号整数范围内。"
        ),
        input_text=(
            "第一行输入 n 和 S（1 <= n <= 200，0 <= S <= 100000，且 n * (S + 1) <= 20000000）。"
            "第二行输入 n 个整数 a_i（0 <= a_i <= 100000）。"
        ),
        output_text="输出元素和恰好为 S 的子集数量。",
        cases=(
            SeedCase("4 5\n1 2 2 3\n", "3\n", is_sample=True),
            SeedCase("3 0\n0 0 1\n", "4\n"),
            SeedCase("4 2\n1 1 1 1\n", "6\n"),
            SeedCase("3 7\n2 4 6\n", "0\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="股票交易 K 次",
        difficulty="hard",
        tags=("动态规划", "股票", "状态机"),
        statement=(
            "给定连续 n 天的股票价格，最多进行 K 笔完整交易。一笔交易必须先在某一天买入，"
            "再在严格更晚的一天卖出；同一时刻最多持有一股，必须卖出后才能再次买入。"
            "可以少于 K 笔交易，也可以完全不交易。求可获得的最大非负利润，"
            "所有中间利润及答案均需使用 64 位有符号整数。"
        ),
        input_text=(
            "第一行输入 n 和 K（1 <= n <= 2000，0 <= K <= 2000，且 n * (K + 1) <= 2000000）。"
            "第二行输入 n 个整数 p_i（0 <= p_i <= 1000000000），表示第 i 天的价格，下标从 1 开始。"
        ),
        output_text="输出最多完成 K 笔交易可获得的最大利润。",
        cases=(
            SeedCase("6 2\n3 2 6 5 0 3\n", "7\n", is_sample=True),
            SeedCase("5 3\n9 7 5 3 1\n", "0\n"),
            SeedCase("5 10\n1 2 3 4 5\n", "4\n"),
            SeedCase("4 1\n2 4 1 7\n", "6\n"),
            SeedCase("5 2\n0 1000000000 0 1000000000 0\n", "2000000000\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="N 皇后计数",
        difficulty="hard",
        tags=("搜索", "回溯", "位运算"),
        statement=(
            "在 n×n 棋盘上放置 n 个皇后，使任意两个皇后都不在同一行、同一列或同一条对角线上。"
            "两个方案只要至少一个皇后的位置不同，就视为不同方案。求合法放置方案总数。"
        ),
        input_text="输入一个整数 n（1 <= n <= 14）。",
        output_text="输出合法的 N 皇后放置方案数。",
        cases=(
            SeedCase("4\n", "2\n", is_sample=True),
            SeedCase("1\n", "1\n"),
            SeedCase("2\n", "0\n"),
            SeedCase("14\n", "365596\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="数独求解",
        difficulty="hard",
        tags=("搜索", "回溯", "数独"),
        statement=(
            "给定一个 9×9 数独。数字 0 表示空格，请把每个空格填为 1 到 9，使每一行、每一列以及"
            "每个 3×3 宫内的数字 1 到 9 都恰好出现一次。每个测试输入都保证恰有一个解。"
        ),
        input_text=(
            "输入 9 行，每行包含 9 个不带空格的数字字符（0 到 9）。0 表示尚未填写的位置。"
        ),
        output_text="输出唯一解，共 9 行；每行输出 9 个不带空格的数字。",
        cases=(
            SeedCase(
                "530070000\n600195000\n098000060\n800060003\n400803001\n700020006\n060000280\n000419005\n000080079\n",
                "534678912\n672195348\n198342567\n859761423\n426853791\n713924856\n961537284\n287419635\n345286179\n",
                is_sample=True,
            ),
            SeedCase(
                "034678912\n672195348\n198342567\n859761423\n426853791\n713924856\n961537284\n287419635\n345286179\n",
                "534678912\n672195348\n198342567\n859761423\n426853791\n713924856\n961537284\n287419635\n345286179\n",
            ),
            SeedCase(
                "534678000\n672195000\n198342060\n859760003\n426853001\n713924006\n961537280\n287419605\n345286079\n",
                "534678912\n672195348\n198342567\n859761423\n426853791\n713924856\n961537284\n287419635\n345286179\n",
            ),
            SeedCase(
                "530678912\n602195348\n198302567\n859761403\n426853791\n713924856\n961537284\n287419635\n345286179\n",
                "534678912\n672195348\n198342567\n859761423\n426853791\n713924856\n961537284\n287419635\n345286179\n",
            ),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="单词搜索路径",
        difficulty="hard",
        tags=("搜索", "回溯", "网格"),
        statement=(
            "给定一个大写英文字母网格和一个目标单词，判断能否从某个格子出发，依次经过上下左右"
            "四邻接的格子拼出该单词。同一条路径中每个格子最多使用一次。"
        ),
        input_text=(
            "第一行输入 n 和 m（1 <= n,m <= 20，n*m <= 200）。接下来 n 行每行输入一个长度为 m 的"
            "大写字母串，表示网格。最后一行输入长度在 1 到 n*m 之间的目标单词。"
        ),
        output_text="若存在符合要求的路径，输出 Yes；否则输出 No。",
        cases=(
            SeedCase("3 4\nABCE\nSFCS\nADEE\nABCCED\n", "Yes\n", is_sample=True),
            SeedCase("3 4\nABCE\nSFCS\nADEE\nABCB\n", "No\n"),
            SeedCase("1 1\nA\nA\n", "Yes\n"),
            SeedCase("2 2\nAB\nCD\nACDB\n", "Yes\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="双向搜索单词阶梯",
        difficulty="hard",
        tags=("搜索", "双向广度优先搜索", "字符串"),
        statement=(
            "给定起点单词、终点单词和一个词典。每一步可以把当前单词的恰好一个字母改成另一个"
            "小写英文字母。除起点外，序列中的每个单词（包括终点）都必须在词典中。"
            "求包含起点和终点的最短转换序列长度；若无法转换，输出 0。"
        ),
        input_text=(
            "第一行输入起点单词和终点单词，它们是等长的小写字母串，长度为 L"
            "（1 <= L <= 20）。第二行输入词典大小 n（1 <= n <= 50000）。接下来 n 行每行一个"
            "长度为 L 的小写单词，词典中的单词互不相同。"
        ),
        output_text="输出包含起点与终点的最短转换序列长度；不可达时输出 0。",
        cases=(
            SeedCase(
                "hit cog\n6\nhot\ndot\ndog\nlot\nlog\ncog\n",
                "5\n",
                is_sample=True,
            ),
            SeedCase("hit cog\n5\nhot\ndot\ndog\nlot\nlog\n", "0\n"),
            SeedCase("aaa bbb\n4\naab\nabb\nbbb\naba\n", "4\n"),
            SeedCase("a c\n1\nc\n", "2\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="并查集连通性",
        difficulty="hard",
        tags=("数据结构", "并查集", "连通性"),
        statement=(
            "维护 n 个元素之间的连通关系。UNION u v 把 u、v 所在的两个集合合并；"
            "QUERY u v 询问 u 与 v 当前是否属于同一集合。初始时每个元素各自构成一个集合。"
        ),
        input_text=(
            "第一行输入 n 和 q（1 <= n <= 200000，1 <= q <= 300000）。接下来 q 行，每行是"
            " UNION u v 或 QUERY u v（1 <= u,v <= n）。"
        ),
        output_text="对每条 QUERY 操作依次输出一行：连通输出 Yes，否则输出 No。UNION 不输出。",
        cases=(
            SeedCase(
                "5 7\nQUERY 1 2\nUNION 1 2\nQUERY 1 2\nUNION 2 3\nQUERY 1 3\nQUERY 4 5\nUNION 4 5\n",
                "No\nYes\nYes\nNo\n",
                is_sample=True,
            ),
            SeedCase("1 3\nQUERY 1 1\nUNION 1 1\nQUERY 1 1\n", "Yes\nYes\n"),
            SeedCase(
                "6 8\nUNION 1 2\nUNION 3 4\nUNION 2 3\nQUERY 1 4\nQUERY 1 5\nUNION 5 6\nQUERY 4 6\nQUERY 5 6\n",
                "Yes\nNo\nNo\nYes\n",
            ),
            SeedCase(
                "4 7\nUNION 1 2\nUNION 1 2\nQUERY 2 1\nUNION 2 3\nUNION 1 3\nQUERY 1 3\nQUERY 1 4\n",
                "Yes\nYes\nNo\n",
            ),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="带权并查集关系",
        difficulty="hard",
        tags=("数据结构", "带权并查集", "势能差"),
        statement=(
            "维护 n 个未知整数 value[1..n] 之间的差值关系。ADD x y d 表示加入关系"
            " value[y]-value[x]=d，所有新增关系保证与已有关系一致。ASK x y 询问"
            " value[y]-value[x]；若二者之间无法由已知关系推出差值，则输出 UNKNOWN。"
        ),
        input_text=(
            "第一行输入 n 和 q（1 <= n <= 200000，1 <= q <= 300000）。接下来 q 行，每行是"
            " ADD x y d 或 ASK x y（1 <= x,y <= n，-9000000000000000000 <= d <= "
            "9000000000000000000）。输入保证所有关系、可推出的差值和答案都在 64 位有符号整数范围内。"
        ),
        output_text=(
            "对每条 ASK 操作输出一行：若连通，输出 value[y]-value[x]；否则输出 UNKNOWN。ADD 不输出。"
        ),
        cases=(
            SeedCase(
                "4 7\nADD 1 2 5\nADD 2 3 -2\nASK 1 3\nASK 3 1\nASK 1 4\nADD 3 4 10\nASK 2 4\n",
                "3\n-3\nUNKNOWN\n8\n",
                is_sample=True,
            ),
            SeedCase(
                "2 4\nASK 1 1\nASK 1 2\nADD 1 2 4000000000000000000\nASK 2 1\n",
                "0\nUNKNOWN\n-4000000000000000000\n",
            ),
            SeedCase(
                "5 7\nADD 1 2 -7\nADD 2 3 -8\nASK 1 3\nADD 4 5 9\nASK 3 5\nADD 3 4 20\nASK 2 5\n",
                "-15\nUNKNOWN\n21\n",
            ),
            SeedCase(
                "4 7\nADD 1 2 3\nADD 3 4 10\nADD 2 4 5\nASK 1 3\nASK 3 1\nADD 1 4 8\nASK 2 3\n",
                "-2\n2\n-5\n",
            ),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="合并 K 个有序序列",
        difficulty="hard",
        tags=("数据结构", "优先队列", "多路归并"),
        statement=(
            "给定 k 个分别按非降序排列的整数序列，把它们合并成一个包含全部元素的非降序序列。"
            "相同数值出现多次时必须全部保留；输入序列可以为空。"
        ),
        input_text=(
            "第一行输入 k（1 <= k <= 100000）。接下来 k 行，每行先输入该序列长度 len"
            "（0 <= len），再输入 len 个按非降序排列的整数。所有序列的长度之和不超过 300000，"
            "元素均在 64 位有符号整数范围内。"
        ),
        output_text=(
            "在一行中输出合并后的全部整数，以单个空格分隔；若所有序列都为空，输出一个空行。"
        ),
        cases=(
            SeedCase(
                "3\n3 1 4 7\n3 2 2 8\n2 3 6\n",
                "1 2 2 3 4 6 7 8\n",
                is_sample=True,
            ),
            SeedCase("3\n0\n2 -1 5\n0\n", "-1 5\n"),
            SeedCase("1\n0\n", "\n"),
            SeedCase(
                "3\n3 -9000000000000000000 0 7\n2 -9000000000000000000 8\n3 7 7 9000000000000000000\n",
                "-9000000000000000000 -9000000000000000000 0 7 7 7 8 9000000000000000000\n",
            ),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="树状数组区间和",
        difficulty="hard",
        tags=("数据结构", "树状数组", "前缀和"),
        statement=(
            "维护一个下标从 1 开始的整数数组。ADD i delta 把 a[i] 增加 delta；"
            "SUM l r 询问当前闭区间 [l,r] 内所有元素之和。"
        ),
        input_text=(
            "第一行输入 n 和 q（1 <= n,q <= 300000）。第二行输入 n 个初始整数 a_i。"
            "接下来 q 行，每行是 ADD i delta 或 SUM l r（1 <= i <= n，1 <= l <= r <= n）。"
            "初值、delta、所有中间值与区间和均在 64 位有符号整数范围内。"
        ),
        output_text="对每条 SUM 操作依次输出一行闭区间和。ADD 不输出。",
        cases=(
            SeedCase(
                "5 6\n1 2 3 4 5\nSUM 1 5\nADD 3 10\nSUM 2 4\nADD 1 -1\nSUM 1 1\nSUM 3 5\n",
                "15\n19\n0\n22\n",
                is_sample=True,
            ),
            SeedCase("1 4\n-5\nSUM 1 1\nADD 1 8\nSUM 1 1\nSUM 1 1\n", "-5\n3\n3\n"),
            SeedCase(
                "3 4\n3000000000000000000 2000000000000000000 -1000000000000000000\nSUM 1 2\nADD 3 2000000000000000000\nSUM 1 3\nSUM 3 3\n",
                "5000000000000000000\n6000000000000000000\n1000000000000000000\n",
            ),
            SeedCase(
                "4 6\n0 0 0 0\nADD 2 -7\nADD 4 5\nSUM 1 4\nSUM 2 3\nADD 2 7\nSUM 2 4\n",
                "-2\n-7\n5\n",
            ),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="LRU 缓存模拟",
        difficulty="hard",
        tags=("数据结构", "哈希表", "双向链表"),
        statement=(
            "模拟一个固定容量的最近最少使用缓存。GET key：若 key 存在，输出对应 value，并把该 key"
            "变为最近使用；否则输出 -1。PUT key value：插入或更新键值，并把该 key 变为最近使用；"
            "若插入后超过容量，淘汰最久未使用的 key。PUT 不产生输出。"
        ),
        input_text=(
            "第一行输入容量 capacity 和操作数 q（1 <= capacity <= 100000，1 <= q <= 300000）。"
            "接下来 q 行，每行是 GET key 或 PUT key value。key 与 value 均在 64 位有符号整数范围内。"
        ),
        output_text="对每条 GET 操作依次输出一行查询结果；未命中输出 -1。",
        cases=(
            SeedCase(
                "2 9\nPUT 1 1\nPUT 2 2\nGET 1\nPUT 3 3\nGET 2\nPUT 4 4\nGET 1\nGET 3\nGET 4\n",
                "1\n-1\n-1\n3\n4\n",
                is_sample=True,
            ),
            SeedCase(
                "1 6\nPUT 7 10\nGET 7\nPUT 7 20\nPUT 8 30\nGET 7\nGET 8\n",
                "10\n-1\n30\n",
            ),
            SeedCase(
                "2 7\nPUT 1 10\nPUT 2 20\nPUT 1 11\nPUT 3 30\nGET 1\nGET 2\nGET 3\n",
                "11\n-1\n30\n",
            ),
            SeedCase(
                "2 6\nGET 9000000000000000000\nPUT -9000000000000000000 4000000000000000000\nGET -9000000000000000000\nPUT 0 8\nGET 0\nGET -9000000000000000000\n",
                "-1\n4000000000000000000\n8\n4000000000000000000\n",
            ),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="列车时刻冲突",
        difficulty="hard",
        tags=("模拟", "排序", "扫描线"),
        statement=(
            "给定 n 列火车占用同一站台的到达和离开时刻。第 i 列火车占用半开区间"
            " [arrival_i,departure_i)，两列火车的占用区间有非空交集时称为一对冲突。"
            "统计发生冲突的无序火车对数。端点恰好相接不冲突，每对火车最多计数一次。"
        ),
        input_text=(
            "第一行输入 n（1 <= n <= 200000）。接下来 n 行每行输入 arrival_i 和 departure_i"
            "（0 <= arrival_i < departure_i <= 1000000000）。答案保证在 64 位有符号整数范围内。"
        ),
        output_text="输出发生重叠的无序火车对数，答案使用 64 位有符号整数。",
        cases=(
            SeedCase(
                "5\n1 4\n2 5\n4 6\n5 7\n3 8\n",
                "7\n",
                is_sample=True,
            ),
            SeedCase("4\n0 1\n1 2\n2 3\n3 4\n", "0\n"),
            SeedCase("4\n10 20\n10 20\n10 20\n10 20\n", "6\n"),
            SeedCase("1\n0 1000000000\n", "0\n"),
        ),
        time_limit_ms=2000,
    ),
    SeedProblem(
        title="带括号表达式求值",
        difficulty="hard",
        tags=("模拟", "栈", "表达式求值"),
        statement=(
            "计算一个由非负十进制整数、二元运算符 +、-、*、/ 和圆括号组成的合法表达式。"
            "运算遵循标准优先级：括号最高，乘除高于加减；同级运算从左到右结合。表达式不含一元"
            "运算。所有除数均非零，且每次整数除法都能整除；结果与所有中间值均在 64 位有符号整数范围内。"
        ),
        input_text=(
            "输入一行不含空格的合法表达式，长度在 1 到 200000 之间。整数由一个或多个数字组成。"
        ),
        output_text="输出表达式的 64 位有符号整数结果。",
        cases=(
            SeedCase("2*(3+4)-18/3\n", "8\n", is_sample=True),
            SeedCase("42\n", "42\n"),
            SeedCase("8/2/2+3*4\n", "14\n"),
            SeedCase(
                "3000000000*(2000000000-1)\n",
                "5999999997000000000\n",
            ),
        ),
        time_limit_ms=2000,
    ),
)
