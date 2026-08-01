"""Legacy easy seed problems."""
from __future__ import annotations

from .types import SeedCase, SeedProblem


EASY_PROBLEMS: tuple[SeedProblem, ...] = (
    SeedProblem(
        title="两数之和",
        difficulty="easy",
        tags=("基础", "数学"),
        statement="读入两个整数，输出它们的和。",
        input_text="一行两个整数 a、b。",
        output_text="输出 a+b。",
        cases=(
            SeedCase("1 2\n", "3\n", is_sample=True),
            SeedCase("-5 8\n", "3\n"),
        ),
        legacy=True,
    ),
    SeedProblem(
        title="奇偶判断",
        difficulty="easy",
        tags=("基础", "分支"),
        statement="判断一个整数是奇数还是偶数。",
        input_text="一个整数 n。",
        output_text="偶数输出 Even，否则输出 Odd。",
        cases=(
            SeedCase("8\n", "Even\n", is_sample=True),
            SeedCase("-3\n", "Odd\n"),
        ),
        legacy=True,
    ),
    SeedProblem(
        title="区间求和",
        difficulty="easy",
        tags=("循环", "数学"),
        statement="计算闭区间 [l,r] 内所有整数之和。",
        input_text="两个整数 l、r，且 l≤r。",
        output_text="输出区间和。",
        cases=(
            SeedCase("1 5\n", "15\n", is_sample=True),
            SeedCase("-2 2\n", "0\n"),
        ),
        legacy=True,
    ),
    SeedProblem(
        title="两数之积",
        difficulty="easy",
        tags=("基础", "数学"),
        statement=(
            "读入两个整数 a 和 b，计算并输出它们的乘积。"
            "保证 -10^9≤a,b≤10^9，乘积在有符号 64 位整数范围内，请使用 64 位整数保存结果。"
        ),
        input_text="一行输入两个整数 a、b（-10^9≤a,b≤10^9）。",
        output_text="输出一个整数，表示 a×b。",
        cases=(
            SeedCase("12 -7\n", "-84\n", is_sample=True),
            SeedCase("0 999999999\n", "0\n"),
            SeedCase("-1000000000 -1000000000\n", "1000000000000000000\n"),
            SeedCase("1000000000 -1000000000\n", "-1000000000000000000\n"),
        ),
    ),
    SeedProblem(
        title="商与余数",
        difficulty="easy",
        tags=("基础", "数学"),
        statement=(
            "给定非负整数 a 和正整数 b，计算 a 除以 b 的整数商 q 与余数 r。"
            "保证 0≤a≤10^18、1≤b≤10^9。"
            "这里 q=⌊a/b⌋，r=a-q×b，因此 0≤r<b。"
        ),
        input_text="一行输入两个整数 a、b（0≤a≤10^18，1≤b≤10^9）。",
        output_text="一行输出两个整数 q、r，用一个空格分隔，依次表示整数商和余数。",
        cases=(
            SeedCase("17 5\n", "3 2\n", is_sample=True),
            SeedCase("0 7\n", "0 0\n"),
            SeedCase("4 9\n", "0 4\n"),
            SeedCase("1000000000000000000 1\n", "1000000000000000000 0\n"),
        ),
    ),
    SeedProblem(
        title="长方形周长与面积",
        difficulty="easy",
        tags=("基础", "数学"),
        statement=(
            "给定长方形的正整数长 a 和宽 b，计算周长 2×(a+b) 与面积 a×b。"
            "保证 1≤a,b≤10^9，两个答案均在有符号 64 位整数范围内，请使用 64 位整数计算。"
        ),
        input_text="一行输入两个整数 a、b（1≤a,b≤10^9），分别表示长和宽。",
        output_text="一行输出两个整数，用一个空格分隔，依次为长方形的周长和面积。",
        cases=(
            SeedCase("3 5\n", "16 15\n", is_sample=True),
            SeedCase("1 1\n", "4 1\n"),
            SeedCase("1000000000 1000000000\n", "4000000000 1000000000000000000\n"),
            SeedCase("1000000000 1\n", "2000000002 1000000000\n"),
        ),
    ),
    SeedProblem(
        title="秒数转换",
        difficulty="easy",
        tags=("基础", "模拟"),
        statement=(
            "给定一段非负的总秒数 s（0≤s≤10^9），将它转换成小时、分钟和秒。"
            "小时数可以大于 23，不按一天取模；分钟和秒都在 0 到 59 之间。"
        ),
        input_text="输入一个整数 s（0≤s≤10^9），表示总秒数。",
        output_text="一行输出三个整数 h、m、sec，用空格分隔，满足 s=3600h+60m+sec，且 0≤m,sec≤59。",
        cases=(
            SeedCase("3661\n", "1 1 1\n", is_sample=True),
            SeedCase("0\n", "0 0 0\n"),
            SeedCase("59\n", "0 0 59\n"),
            SeedCase("90061\n", "25 1 1\n"),
            SeedCase("60\n", "0 1 0\n"),
            SeedCase("3600\n", "1 0 0\n"),
        ),
    ),
    SeedProblem(
        title="整数数位分解",
        difficulty="easy",
        tags=("基础", "数学"),
        statement=(
            "给定一个五位正整数 n（10000≤n≤99999），按从最高位到最低位的顺序输出它的每一位数字。"
            "输入固定为五位数，因此没有前导零；十进制表示中间出现的零必须原样输出。"
        ),
        input_text="输入一个整数 n（10000≤n≤99999）。",
        output_text="一行输出五个数字，用单个空格分隔，依次为万位、千位、百位、十位和个位。",
        cases=(
            SeedCase("12345\n", "1 2 3 4 5\n", is_sample=True),
            SeedCase("10000\n", "1 0 0 0 0\n"),
            SeedCase("90706\n", "9 0 7 0 6\n"),
            SeedCase("99999\n", "9 9 9 9 9\n"),
        ),
    ),
    SeedProblem(
        title="三数最大值",
        difficulty="easy",
        tags=("基础", "分支"),
        statement=(
            "给定三个整数 a、b、c（-10^18≤a,b,c≤10^18），输出其中的最大值。"
            "三个数可以相等，答案保证在有符号 64 位整数范围内。"
        ),
        input_text="一行输入三个整数 a、b、c（-10^18≤a,b,c≤10^18）。",
        output_text="输出一个整数，表示三个数中的最大值。",
        cases=(
            SeedCase("3 9 5\n", "9\n", is_sample=True),
            SeedCase("-7 -2 -11\n", "-2\n"),
            SeedCase("1000000000000000000 0 999999999999999999\n", "1000000000000000000\n"),
            SeedCase("4 4 4\n", "4\n"),
        ),
    ),
    SeedProblem(
        title="成绩等级",
        difficulty="easy",
        tags=("基础", "分支"),
        statement=(
            "给定一个整数成绩 s（0≤s≤100），按闭区间评定等级："
            "90≤s≤100 为 A，80≤s≤89 为 B，70≤s≤79 为 C，"
            "60≤s≤69 为 D，0≤s≤59 为 F。"
        ),
        input_text="输入一个整数 s（0≤s≤100）。",
        output_text="输出一个大写字母 A、B、C、D 或 F，表示对应等级。",
        cases=(
            SeedCase("100\n", "A\n", is_sample=True),
            SeedCase("89\n", "B\n"),
            SeedCase("70\n", "C\n"),
            SeedCase("60\n", "D\n"),
            SeedCase("59\n", "F\n"),
            SeedCase("0\n", "F\n"),
            SeedCase("90\n", "A\n"),
            SeedCase("80\n", "B\n"),
        ),
    ),
    SeedProblem(
        title="闰年判断",
        difficulty="easy",
        tags=("基础", "分支"),
        statement=(
            "给定公历年份 y（1≤y≤9999），判断它是否为闰年。"
            "若 y 能被 400 整除，或者能被 4 整除但不能被 100 整除，则是闰年。"
        ),
        input_text="输入一个整数 y（1≤y≤9999），表示公历年份。",
        output_text="若 y 是闰年输出 Yes，否则输出 No。",
        cases=(
            SeedCase("2000\n", "Yes\n", is_sample=True),
            SeedCase("1900\n", "No\n"),
            SeedCase("2024\n", "Yes\n"),
            SeedCase("2023\n", "No\n"),
            SeedCase("1\n", "No\n"),
        ),
    ),
    SeedProblem(
        title="三角形判定",
        difficulty="easy",
        tags=("基础", "分支"),
        statement=(
            "给定三个正整数边长 a、b、c（1≤a,b,c≤10^9），判断它们能否组成非退化三角形。"
            "当且仅当任意两边之和都严格大于第三边时可以组成；边长上限保证用有符号 64 位整数求和不会溢出。"
        ),
        input_text="一行输入三个正整数 a、b、c（1≤a,b,c≤10^9）。",
        output_text="若能组成非退化三角形输出 Yes，否则输出 No。",
        cases=(
            SeedCase("3 4 5\n", "Yes\n", is_sample=True),
            SeedCase("1 2 3\n", "No\n"),
            SeedCase("2 2 3\n", "Yes\n"),
            SeedCase("1000000000 1000000000 1000000000\n", "Yes\n"),
            SeedCase("10 1 2\n", "No\n"),
        ),
    ),
    SeedProblem(
        title="阶乘",
        difficulty="easy",
        tags=("循环", "数学"),
        statement=(
            "给定整数 n（0≤n≤20），计算 n 的阶乘 n!=1×2×⋯×n。"
            "特别规定 0!=1；20! 及更小的结果均在有符号 64 位整数范围内。"
        ),
        input_text="输入一个整数 n（0≤n≤20）。",
        output_text="输出一个整数，表示 n!。",
        cases=(
            SeedCase("5\n", "120\n", is_sample=True),
            SeedCase("0\n", "1\n"),
            SeedCase("1\n", "1\n"),
            SeedCase("20\n", "2432902008176640000\n"),
            SeedCase("10\n", "3628800\n"),
        ),
    ),
    SeedProblem(
        title="质数判断",
        difficulty="easy",
        tags=("循环", "数学"),
        statement=(
            "给定整数 n（-10^9≤n≤10^9），判断 n 是否为质数。"
            "质数是大于等于 2 且只有 1 和自身两个正约数的整数，因此所有 n<2 的数都不是质数。"
        ),
        input_text="输入一个整数 n（-10^9≤n≤10^9）。",
        output_text="若 n 是质数输出 Yes，否则输出 No。",
        cases=(
            SeedCase("17\n", "Yes\n", is_sample=True),
            SeedCase("1\n", "No\n"),
            SeedCase("-7\n", "No\n"),
            SeedCase("2\n", "Yes\n"),
            SeedCase("49\n", "No\n"),
            SeedCase("1000000000\n", "No\n"),
            SeedCase("999999937\n", "Yes\n"),
        ),
    ),
    SeedProblem(
        title="约数个数",
        difficulty="easy",
        tags=("循环", "数学"),
        statement=(
            "给定正整数 n（1≤n≤10^12），统计能整除 n 的正整数个数。"
            "只统计正约数；可以枚举到 √n，并把成对约数同时计入，完全平方数的平方根只计一次。"
        ),
        input_text="输入一个正整数 n（1≤n≤10^12）。",
        output_text="输出一个整数，表示 n 的正约数个数。",
        cases=(
            SeedCase("12\n", "6\n", is_sample=True),
            SeedCase("1\n", "1\n"),
            SeedCase("36\n", "9\n"),
            SeedCase("999983\n", "2\n"),
            SeedCase("1000000000000\n", "169\n"),
        ),
    ),
    SeedProblem(
        title="数字反转",
        difficulty="easy",
        tags=("循环", "数学"),
        statement=(
            "给定非负整数 n（0≤n≤10^18），将其十进制数字顺序反转后输出。"
            "反转结果不保留前导零，例如 1200 反转为 21；当 n=0 时输出 0。"
        ),
        input_text="输入一个非负整数 n（0≤n≤10^18），输入本身不含多余前导零。",
        output_text="输出一个非负整数，表示按规则得到的反转结果。",
        cases=(
            SeedCase("12340\n", "4321\n", is_sample=True),
            SeedCase("0\n", "0\n"),
            SeedCase("1000\n", "1\n"),
            SeedCase("1200300\n", "30021\n"),
            SeedCase("1000000000000000000\n", "1\n"),
        ),
    ),
    SeedProblem(
        title="完全数判断",
        difficulty="easy",
        tags=("循环", "数学"),
        statement=(
            "给定正整数 n（1≤n≤10^8），判断它是否为完全数。"
            "完全数等于其所有小于自身的正约数之和；例如 6 的真因子为 1、2、3，且 1+2+3=6。"
        ),
        input_text="输入一个正整数 n（1≤n≤10^8）。",
        output_text="若 n 是完全数输出 Yes，否则输出 No。",
        cases=(
            SeedCase("6\n", "Yes\n", is_sample=True),
            SeedCase("28\n", "Yes\n"),
            SeedCase("1\n", "No\n"),
            SeedCase("12\n", "No\n"),
            SeedCase("33550336\n", "Yes\n"),
        ),
    ),
    SeedProblem(
        title="斐波那契第 N 项",
        difficulty="easy",
        tags=("循环", "数学"),
        statement=(
            "斐波那契数列定义为 F0=0、F1=1，并且当 n≥2 时 Fn=F(n-1)+F(n-2)。"
            "给定 n（0≤n≤92），输出 Fn；该范围内的结果均在有符号 64 位整数范围内。"
        ),
        input_text="输入一个整数 n（0≤n≤92）。",
        output_text="输出一个整数，表示斐波那契数列的 Fn。",
        cases=(
            SeedCase("10\n", "55\n", is_sample=True),
            SeedCase("0\n", "0\n"),
            SeedCase("1\n", "1\n"),
            SeedCase("2\n", "1\n"),
            SeedCase("92\n", "7540113804746346429\n"),
        ),
    ),
    SeedProblem(
        title="数组最大值",
        difficulty="easy",
        tags=("数组", "基础"),
        statement=(
            "给定一个长度为 n 的整数数组（1≤n≤10^5），求数组中的最大值。"
            "每个元素 ai 都满足 -10^18≤ai≤10^18，答案可用有符号 64 位整数保存。"
        ),
        input_text=(
            "第一行输入整数 n（1≤n≤10^5）。第二行输入 n 个整数 a1,a2,…,an"
            "（-10^18≤ai≤10^18），相邻整数以空格分隔。"
        ),
        output_text="输出一个整数，表示数组中的最大值。",
        cases=(
            SeedCase("5\n3 -7 12 12 0\n", "12\n", is_sample=True),
            SeedCase("1\n-1000000000000000000\n", "-1000000000000000000\n"),
            SeedCase("4\n-5 -5 -5 -5\n", "-5\n"),
            SeedCase(
                "6\n-1000000000000000000 0 999999999999999999 -2 8 7\n",
                "999999999999999999\n",
            ),
        ),
    ),
    SeedProblem(
        title="数组逆序",
        difficulty="easy",
        tags=("数组", "基础"),
        statement=(
            "给定一个长度为 n 的整数数组（1≤n≤10^5），将全部元素按输入顺序反转后输出。"
            "也就是说，原来的第 i 个元素将出现在第 n-i+1 个位置；位置编号从 1 开始。"
        ),
        input_text=(
            "第一行输入整数 n（1≤n≤10^5）。第二行输入 n 个整数 a1,a2,…,an"
            "（-10^9≤ai≤10^9）。"
        ),
        output_text="一行输出逆序后的 n 个整数，相邻整数之间用一个空格分隔。",
        cases=(
            SeedCase("5\n1 2 3 4 5\n", "5 4 3 2 1\n", is_sample=True),
            SeedCase("1\n-7\n", "-7\n"),
            SeedCase("4\n0 -1 0 8\n", "8 0 -1 0\n"),
            SeedCase("6\n2 2 3 3 4 4\n", "4 4 3 3 2 2\n"),
        ),
    ),
    SeedProblem(
        title="统计正负零",
        difficulty="easy",
        tags=("数组", "计数"),
        statement=(
            "给定一个长度为 n 的整数数组（1≤n≤10^5），分别统计其中正数、负数和零的个数。"
            "正数指严格大于 0 的数，负数指严格小于 0 的数。"
        ),
        input_text=(
            "第一行输入整数 n（1≤n≤10^5）。第二行输入 n 个整数 a1,a2,…,an"
            "（-10^18≤ai≤10^18）。"
        ),
        output_text="一行输出三个非负整数，依次为正数、负数、零的个数，用一个空格分隔。",
        cases=(
            SeedCase("7\n-2 0 5 -1 0 8 3\n", "3 2 2\n", is_sample=True),
            SeedCase("4\n0 0 0 0\n", "0 0 4\n"),
            SeedCase("3\n-1 -2 -3\n", "0 3 0\n"),
            SeedCase(
                "5\n-1000000000000000000 1000000000000000000 1 -1 0\n",
                "2 2 1\n",
            ),
        ),
    ),
    SeedProblem(
        title="删除指定元素",
        difficulty="easy",
        tags=("数组", "模拟"),
        statement=(
            "给定长度为 n 的整数数组和整数 x（1≤n≤10^5），删除数组中所有等于 x 的元素，"
            "并保持其余元素的相对顺序不变。若删除后没有剩余元素，输出 EMPTY。"
        ),
        input_text=(
            "第一行输入两个整数 n、x（1≤n≤10^5，-10^9≤x≤10^9）。"
            "第二行输入 n 个整数 a1,a2,…,an（-10^9≤ai≤10^9）。"
        ),
        output_text=(
            "若有剩余元素，在一行中按原顺序输出它们，相邻整数用一个空格分隔；"
            "若全部元素都被删除，仅输出大写字符串 EMPTY。"
        ),
        cases=(
            SeedCase("7 2\n2 1 2 3 2 4 2\n", "1 3 4\n", is_sample=True),
            SeedCase("3 -5\n-5 -5 -5\n", "EMPTY\n"),
            SeedCase("4 9\n1 2 3 4\n", "1 2 3 4\n"),
            SeedCase("6 0\n0 -1 0 2 3 0\n", "-1 2 3\n"),
        ),
    ),
    SeedProblem(
        title="数组循环右移",
        difficulty="easy",
        tags=("数组", "模拟"),
        statement=(
            "给定长度为 n 的整数数组和非负整数 k（1≤n≤10^5，0≤k≤10^18），"
            "将数组循环向右移动 k 次。一次右移会把最后一个元素移到第一个位置，"
            "其余元素依次右移一位；当 k 大于 n 时按 k mod n 次处理。"
        ),
        input_text=(
            "第一行输入两个整数 n、k（1≤n≤10^5，0≤k≤10^18）。"
            "第二行输入 n 个整数 a1,a2,…,an（-10^9≤ai≤10^9）。"
        ),
        output_text="一行输出循环右移后的 n 个整数，相邻整数之间用一个空格分隔。",
        cases=(
            SeedCase("5 2\n1 2 3 4 5\n", "4 5 1 2 3\n", is_sample=True),
            SeedCase("4 10\n-1 0 2 8\n", "2 8 -1 0\n"),
            SeedCase("3 0\n7 8 9\n", "7 8 9\n"),
            SeedCase("1 1000000000000000000\n42\n", "42\n"),
        ),
    ),
    SeedProblem(
        title="第二大不同值",
        difficulty="easy",
        tags=("数组", "基础"),
        statement=(
            "给定一个长度为 n 的整数数组（1≤n≤10^5），求严格小于数组最大值的最大元素，"
            "即第二大的不同值。相同数值只算一种；若数组中少于两个不同值，输出 NONE。"
        ),
        input_text=(
            "第一行输入整数 n（1≤n≤10^5）。第二行输入 n 个整数 a1,a2,…,an"
            "（-10^18≤ai≤10^18）。"
        ),
        output_text="若存在第二大的不同值，输出该整数；否则仅输出大写字符串 NONE。",
        cases=(
            SeedCase("6\n5 1 5 3 3 4\n", "4\n", is_sample=True),
            SeedCase("4\n7 7 7 7\n", "NONE\n"),
            SeedCase("5\n-8 -2 -2 -5 -8\n", "-5\n"),
            SeedCase(
                "4\n-1000000000000000000 1000000000000000000 0 1000000000000000000\n",
                "0\n",
            ),
        ),
    ),
    SeedProblem(
        title="有序数组合并",
        difficulty="easy",
        tags=("数组", "双指针"),
        statement=(
            "给定两个分别含 n 和 m 个整数的非递减数组（1≤n,m，n+m≤2×10^5），"
            "将它们合并为一个非递减数组。两个输入数组中的每次出现都必须保留，"
            "包括来自同一数组或不同数组的重复值。"
        ),
        input_text=(
            "第一行输入两个整数 n、m（1≤n,m，n+m≤2×10^5）。"
            "第二行输入非递减数组 a 的 n 个整数，第三行输入非递减数组 b 的 m 个整数；"
            "所有元素均满足 -10^9≤值≤10^9。"
        ),
        output_text="一行输出合并后的 n+m 个整数，保持非递减顺序，相邻整数用一个空格分隔。",
        cases=(
            SeedCase("4 5\n1 3 3 8\n2 3 6 8 9\n", "1 2 3 3 3 6 8 8 9\n", is_sample=True),
            SeedCase("3 2\n-5 -2 0\n1 4\n", "-5 -2 0 1 4\n"),
            SeedCase("1 3\n7\n7 7 7\n", "7 7 7 7\n"),
            SeedCase("3 3\n-3 0 9\n-4 0 10\n", "-4 -3 0 0 9 10\n"),
        ),
    ),
    SeedProblem(
        title="矩阵转置",
        difficulty="easy",
        tags=("数组", "矩阵"),
        statement=(
            "给定一个 r 行 c 列的整数矩阵 A（1≤r,c，r×c≤10^5），输出它的转置矩阵 B。"
            "行、列编号均从 1 开始，转置后 B 有 c 行 r 列，并满足 B[j][i]=A[i][j]。"
        ),
        input_text=(
            "第一行输入两个整数 r、c（1≤r,c，r×c≤10^5）。"
            "接下来 r 行，每行输入 c 个整数，表示矩阵 A；每个元素的绝对值不超过 10^9。"
        ),
        output_text=(
            "输出 c 行，每行 r 个整数，表示转置矩阵 B；每行相邻整数之间用一个空格分隔。"
        ),
        cases=(
            SeedCase("2 3\n1 2 3\n4 5 6\n", "1 4\n2 5\n3 6\n", is_sample=True),
            SeedCase("1 4\n7 0 -2 9\n", "7\n0\n-2\n9\n"),
            SeedCase("3 1\n5\n6\n7\n", "5 6 7\n"),
            SeedCase("2 2\n-1 1000000000\n0 -5\n", "-1 0\n1000000000 -5\n"),
        ),
    ),
    SeedProblem(
        title="字符串长度统计",
        difficulty="easy",
        tags=("字符串", "基础"),
        statement=(
            "读取一整行字符串 s，统计其中的字符个数。s 仅由可打印 ASCII 字符（编码 32 至 126）组成，"
            "长度满足 0≤|s|≤10^5；空格也计入长度，行末用于结束输入的换行符不计入长度。"
        ),
        input_text=(
            "输入仅一行字符串 s（0≤|s|≤10^5），可能为空，也可能包含空格；s 只含编码 32 至 126 的"
            "可打印 ASCII 字符。请用读取整行的方式取得它，并且不要把行末换行符计入 s。"
        ),
        output_text="输出一个非负整数，表示 s 的字符个数（包括 s 中的所有空格）。",
        cases=(
            SeedCase("hello world\n", "11\n", is_sample=True),
            SeedCase("\n", "0\n"),
            SeedCase("  a b  \n", "7\n"),
            SeedCase("123!?\n", "5\n"),
        ),
    ),
    SeedProblem(
        title="回文字符串",
        difficulty="easy",
        tags=("字符串", "双指针"),
        statement=(
            "给定一个非空字符串 s（1≤|s|≤10^5），判断从左到右和从右到左读取是否完全相同。"
            "s 只含大写或小写英文字母，比较时区分大小写，例如 A 与 a 不相同。"
        ),
        input_text="输入一行非空字符串 s（1≤|s|≤10^5），仅由英文字母 A-Z、a-z 组成且不含空格。",
        output_text="若 s 是区分大小写意义下的回文字符串，输出 Yes；否则输出 No。",
        cases=(
            SeedCase("level\n", "Yes\n", is_sample=True),
            SeedCase("a\n", "Yes\n"),
            SeedCase("Aa\n", "No\n"),
            SeedCase("abca\n", "No\n"),
        ),
    ),
    SeedProblem(
        title="字母频次",
        difficulty="easy",
        tags=("字符串", "计数"),
        statement=(
            "给定一个仅由小写英文字母组成的非空字符串 s（1≤|s|≤10^5），"
            "统计每个字母出现的次数，并严格按照 a、b、c、…、z 的顺序输出 26 个计数。"
        ),
        input_text="输入一行字符串 s（1≤|s|≤10^5），只包含小写英文字母 a-z，不含空格。",
        output_text="一行输出 26 个非负整数，按 a 到 z 的顺序表示各字母频次，相邻计数用一个空格分隔。",
        cases=(
            SeedCase(
                "abac\n",
                "2 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n",
                is_sample=True,
            ),
            SeedCase(
                "abcdefghijklmnopqrstuvwxyz\n",
                "1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1\n",
            ),
            SeedCase(
                "zzzz\n",
                "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 4\n",
            ),
            SeedCase(
                "banana\n",
                "3 1 0 0 0 0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0 0 0 0 0\n",
            ),
        ),
    ),
    SeedProblem(
        title="大小写转换",
        difficulty="easy",
        tags=("字符串", "模拟"),
        statement=(
            "读取一整行非空字符串 s（1≤|s|≤10^5），把每个小写英文字母 a-z 转换为对应的"
            "大写字母 A-Z，把每个大写英文字母 A-Z 转换为对应的小写字母 a-z。"
            "数字、空格和其他可打印 ASCII 字符保持原样。"
        ),
        input_text=(
            "输入一行非空字符串 s（1≤|s|≤10^5），由可打印 ASCII 字符（编码 32 至 126）组成，"
            "可能包含空格；请读取整行。"
        ),
        output_text="输出转换后的整行字符串，字符顺序不变，并在末尾输出换行。",
        cases=(
            SeedCase("Hello, World! 123\n", "hELLO, wORLD! 123\n", is_sample=True),
            SeedCase("abcXYZ\n", "ABCxyz\n"),
            SeedCase("123 !?\n", "123 !?\n"),
            SeedCase("AaZz\n", "aAzZ\n"),
        ),
    ),
    SeedProblem(
        title="单词计数",
        difficulty="easy",
        tags=("字符串", "计数"),
        statement=(
            "读取一整行字符串 s（0≤|s|≤10^5），统计其中的单词个数。"
            "本题把单词定义为由一个或多个非空格字符组成的极大连续段；分隔符仅指 ASCII 空格字符，"
            "因此行首、行尾以及连续多个空格都不会产生空单词。"
        ),
        input_text=(
            "输入仅一行字符串 s（0≤|s|≤10^5），可能为空，也可能含有行首、行尾或连续多个空格；"
            "s 中除空格外的字符均为编码 33 至 126 的可打印 ASCII 字符。"
        ),
        output_text="输出一个非负整数，表示按上述定义得到的单词个数。",
        cases=(
            SeedCase("OJ Campus is fun\n", "4\n", is_sample=True),
            SeedCase("  alpha   beta gamma  \n", "3\n"),
            SeedCase("\n", "0\n"),
            SeedCase("a,b  c!\n", "2\n"),
            SeedCase("     \n", "0\n"),
        ),
    ),
    SeedProblem(
        title="删除连续重复字符",
        difficulty="easy",
        tags=("字符串", "模拟"),
        statement=(
            "给定一个非空字符串 s（1≤|s|≤10^5），把每个由相同字符构成的极大连续段缩短为一个字符，"
            "并保持各段的原有顺序。s 只含英文字母，字符比较区分大小写，所以 A 与 a 不属于相同字符。"
        ),
        input_text="输入一行非空字符串 s（1≤|s|≤10^5），仅由英文字母 A-Z、a-z 组成且不含空格。",
        output_text="输出删除连续重复字符后的字符串；每个连续段只保留最左边的一个字符。",
        cases=(
            SeedCase("aaabbcca\n", "abca\n", is_sample=True),
            SeedCase("a\n", "a\n"),
            SeedCase("aAaA\n", "aAaA\n"),
            SeedCase("zzzYYzz\n", "zYz\n"),
        ),
    ),
    SeedProblem(
        title="字符串循环左移",
        difficulty="easy",
        tags=("字符串", "模拟"),
        statement=(
            "给定一个非空字符串 s 和非负整数 k（1≤|s|≤10^5，0≤k≤10^18），"
            "将 s 循环向左移动 k 次。一次左移会把第一个字符移到末尾，其余字符依次左移一位；"
            "当 k 大于字符串长度时按 k mod |s| 次处理。字符大小写及内容均保持不变。"
        ),
        input_text=(
            "第一行输入非空字符串 s（1≤|s|≤10^5），仅由英文字母和数字组成且不含空格。"
            "第二行输入整数 k（0≤k≤10^18）。"
        ),
        output_text="输出循环左移后的字符串，并在末尾输出换行。",
        cases=(
            SeedCase("abcdef\n2\n", "cdefab\n", is_sample=True),
            SeedCase("Code123\n10\n", "e123Cod\n"),
            SeedCase("XYZ\n0\n", "XYZ\n"),
            SeedCase("q\n1000000000000000000\n", "q\n"),
        ),
    ),
    SeedProblem(
        title="数字各位之和",
        difficulty="easy",
        tags=("循环", "数学"),
        statement=(
            "给定非负整数 n（0≤n≤10^18），计算它的十进制表示中所有数字之和。"
            "当 n=0 时，它的十进制表示只有数字 0，因此答案为 0。"
        ),
        input_text="输入一个非负整数 n（0≤n≤10^18），输入不含多余前导零。",
        output_text="输出一个非负整数，表示 n 的十进制各位数字之和。",
        cases=(
            SeedCase("12345\n", "15\n", is_sample=True),
            SeedCase("0\n", "0\n"),
            SeedCase("1000000000000000000\n", "1\n"),
            SeedCase("999999999999999999\n", "162\n"),
        ),
    ),
    SeedProblem(
        title="日期的下一天",
        difficulty="easy",
        tags=("分支", "模拟"),
        statement=(
            "给定一个合法的公历日期 y 年 m 月 d 日（1≤y≤9998），求它的下一天。"
            "1、3、5、7、8、10、12 月有 31 天，4、6、9、11 月有 30 天；"
            "2 月在闰年有 29 天，在普通年有 28 天。若年份能被 400 整除，"
            "或能被 4 整除但不能被 100 整除，则该年为闰年。输入保证日期合法，"
            "且年份上限保证下一天仍在允许的公历年份范围内。"
        ),
        input_text="一行输入三个整数 y、m、d（1≤y≤9998），表示一个保证合法的公历日期。",
        output_text="一行输出三个整数 y、m、d，用一个空格分隔，表示输入日期的下一天。",
        cases=(
            SeedCase("2023 4 30\n", "2023 5 1\n", is_sample=True),
            SeedCase("2023 12 31\n", "2024 1 1\n"),
            SeedCase("2024 2 28\n", "2024 2 29\n"),
            SeedCase("2024 2 29\n", "2024 3 1\n"),
            SeedCase("1900 2 28\n", "1900 3 1\n"),
        ),
    ),
    SeedProblem(
        title="时钟增加分钟",
        difficulty="easy",
        tags=("数学", "模拟"),
        statement=(
            "给定 24 小时制时刻 h 时 m 分和非负整数 delta，将时刻向后增加 delta 分钟。"
            "时钟每 24 小时循环一次；当 delta 超过一天时也按此规则循环。"
        ),
        input_text=(
            "一行输入三个整数 h、m、delta（0≤h≤23，0≤m≤59，0≤delta≤10^18），"
            "分别表示小时、分钟和要增加的分钟数。"
        ),
        output_text="一行输出增加后的小时 h 和分钟 m，用一个空格分隔；输出整数且不补前导零。",
        cases=(
            SeedCase("23 50 20\n", "0 10\n", is_sample=True),
            SeedCase("10 15 0\n", "10 15\n"),
            SeedCase("1 0 1500\n", "2 0\n"),
            SeedCase("0 0 1000000000000000000\n", "10 40\n"),
        ),
    ),
    SeedProblem(
        title="简易计算器",
        difficulty="easy",
        tags=("分支", "模拟"),
        statement=(
            "给定两个整数 a、b 和一个运算符 op，计算表达式 a op b。op 只可能是 +、-、*、/。"
            "当 op 为 / 时保证 b≠0 且 a 能被 b 整除，按 C++ 整数除法得到精确整数结果。"
            "所有输入操作数以及四种运算的结果都保证在有符号 64 位整数范围内。"
        ),
        input_text=(
            "一行依次输入整数 a、字符 op、整数 b，相邻项用空格分隔；"
            "-10^18≤a,b≤10^18，op∈{+,-,*,/}，并满足题面中的除法和范围保证。"
        ),
        output_text="输出一个整数，表示表达式 a op b 的结果。",
        cases=(
            SeedCase("7 + -3\n", "4\n", is_sample=True),
            SeedCase("-10 - 5\n", "-15\n"),
            SeedCase("-7 * -8\n", "56\n"),
            SeedCase("-20 / 4\n", "-5\n"),
        ),
    ),
    SeedProblem(
        title="三的倍数报数",
        difficulty="easy",
        tags=("循环", "模拟"),
        statement=(
            "从 1 到 n 按整数升序依次报数，只把其中能被 3 整除的数写入输出。"
            "也就是说，需要按升序输出所有不超过 n 的正整数 3 的倍数。"
            "如果不存在这样的数，则输出大写字符串 NONE。"
        ),
        input_text="输入一个整数 n（1≤n≤10^5），表示报数的终点。",
        output_text=(
            "若存在 3 的倍数，在一行中按升序输出它们，相邻整数用一个空格分隔；"
            "若不存在，仅输出大写字符串 NONE。"
        ),
        cases=(
            SeedCase("10\n", "3 6 9\n", is_sample=True),
            SeedCase("1\n", "NONE\n"),
            SeedCase("3\n", "3\n"),
            SeedCase("12\n", "3 6 9 12\n"),
        ),
    ),
    SeedProblem(
        title="自动售货机找零",
        difficulty="easy",
        tags=("贪心", "模拟"),
        statement=(
            "自动售货机的商品售价为 price，顾客付款 payment，二者均为整数金额且 payment≥price。"
            "售货机只使用面额 100、50、20、10、5、1 的纸币或硬币找零。"
            "使用从大面额到小面额的贪心方法，可以得到最少的纸币或硬币总数。"
            "请计算每种面额分别需要多少张或枚。"
        ),
        input_text="一行输入两个整数 price、payment（0≤price≤payment≤10^9）。",
        output_text=(
            "一行输出六个非负整数，用一个空格分隔，依次表示面额 100、50、20、10、5、1 的数量。"
        ),
        cases=(
            SeedCase("123 500\n", "3 1 1 0 1 2\n", is_sample=True),
            SeedCase("250 250\n", "0 0 0 0 0 0\n"),
            SeedCase("1 187\n", "1 1 1 1 1 1\n"),
            SeedCase("99 100\n", "0 0 0 0 0 1\n"),
        ),
    ),
    SeedProblem(
        title="电梯运行时间",
        difficulty="easy",
        tags=("数组", "模拟"),
        statement=(
            "电梯最初位于 0 层，并按输入顺序访问 n 个目标楼层。"
            "电梯每上行一层用 6 秒，每下行一层用 4 秒；每到达一个目标都停留 5 秒，"
            "即使该目标与上一个楼层相同也要停留。若当前位置为 cur、下一目标为 x，"
            "则本段耗时为 (x-cur)×6+5（x≥cur）或 (cur-x)×4+5（x<cur）。"
            "总时间是所有段耗时之和。"
        ),
        input_text=(
            "第一行输入整数 n（1≤n≤10^5）。第二行输入 n 个整数 f1,f2,…,fn"
            "（0≤fi≤10^9），表示依次访问的目标楼层；总时间保证在有符号 64 位整数范围内。"
        ),
        output_text="输出一个整数，表示完成全部访问所需的总秒数。",
        cases=(
            SeedCase("3\n2 1 3\n", "43\n", is_sample=True),
            SeedCase("3\n5 5 2\n", "57\n"),
            SeedCase("1\n10\n", "65\n"),
            SeedCase("2\n3 0\n", "40\n"),
        ),
    ),
)
