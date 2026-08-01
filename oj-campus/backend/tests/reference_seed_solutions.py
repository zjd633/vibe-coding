"""Known-correct C++17 solutions for representative seeded problems."""

REFERENCE_SOLUTIONS: dict[str, str] = {
    "长方形周长与面积": r"""
#include <iostream>
using namespace std;
int main() {
    long long a, b;
    cin >> a >> b;
    cout << 2 * (a + b) << ' ' << a * b << '\n';
}
""",
    "闰年判断": r"""
#include <iostream>
using namespace std;
int main() {
    int y;
    cin >> y;
    cout << ((y % 400 == 0 || (y % 4 == 0 && y % 100 != 0)) ? "Yes" : "No") << '\n';
}
""",
    "质数判断": r"""
#include <iostream>
using namespace std;
int main() {
    long long n;
    cin >> n;
    if (n < 2) {
        cout << "No\n";
        return 0;
    }
    for (long long divisor = 2; divisor <= n / divisor; ++divisor) {
        if (n % divisor == 0) {
            cout << "No\n";
            return 0;
        }
    }
    cout << "Yes\n";
}
""",
    "数组循环右移": r"""
#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;
int main() {
    int n;
    long long k;
    cin >> n >> k;
    vector<long long> values(n);
    for (auto &value : values) cin >> value;
    k %= n;
    rotate(values.begin(), values.end() - k, values.end());
    for (int i = 0; i < n; ++i) cout << values[i] << (i + 1 == n ? '\n' : ' ');
}
""",
    "回文字符串": r"""
#include <algorithm>
#include <iostream>
#include <string>
using namespace std;
int main() {
    string value, reversed;
    cin >> value;
    reversed = value;
    reverse(reversed.begin(), reversed.end());
    cout << (value == reversed ? "Yes" : "No") << '\n';
}
""",
    "日期的下一天": r"""
#include <iostream>
using namespace std;
int main() {
    int y, m, d;
    cin >> y >> m >> d;
    int days[] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if (y % 400 == 0 || (y % 4 == 0 && y % 100 != 0)) days[2] = 29;
    if (++d > days[m]) {
        d = 1;
        if (++m > 12) {
            m = 1;
            ++y;
        }
    }
    cout << y << ' ' << m << ' ' << d << '\n';
}
""",
    "二分查找首次出现": r"""
#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<long long> values(n);
    for (auto &value : values) cin >> value;
    long long target;
    cin >> target;
    auto found = lower_bound(values.begin(), values.end(), target);
    cout << (found == values.end() || *found != target ? -1 : int(found - values.begin()) + 1) << '\n';
}
""",
    "区间和查询": r"""
#include <iostream>
#include <vector>
using namespace std;
int main() {
    int n, q;
    cin >> n >> q;
    vector<long long> prefix(n + 1);
    for (int i = 1; i <= n; ++i) {
        long long value;
        cin >> value;
        prefix[i] = prefix[i - 1] + value;
    }
    while (q--) {
        int left, right;
        cin >> left >> right;
        cout << prefix[right] - prefix[left - 1] << '\n';
    }
}
""",
    "后缀表达式求值": r"""
#include <iostream>
#include <string>
#include <vector>
using namespace std;
int main() {
    int count;
    cin >> count;
    vector<long long> stack;
    while (count--) {
        string token;
        cin >> token;
        if (token.size() != 1 || string("+-*/").find(token[0]) == string::npos) {
            stack.push_back(stoll(token));
            continue;
        }
        long long right = stack.back(); stack.pop_back();
        long long left = stack.back(); stack.pop_back();
        if (token[0] == '+') stack.push_back(left + right);
        else if (token[0] == '-') stack.push_back(left - right);
        else if (token[0] == '*') stack.push_back(left * right);
        else stack.push_back(left / right);
    }
    cout << stack.back() << '\n';
}
""",
    "迷宫最短路": r"""
#include <iostream>
#include <queue>
#include <string>
#include <vector>
using namespace std;
int main() {
    int n, m;
    cin >> n >> m;
    vector<string> grid(n);
    for (auto &row : grid) cin >> row;
    int sx, sy, tx, ty;
    cin >> sx >> sy >> tx >> ty;
    --sx; --sy; --tx; --ty;
    vector<vector<int>> distance(n, vector<int>(m, -1));
    queue<pair<int, int>> pending;
    distance[sx][sy] = 0;
    pending.push({sx, sy});
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    while (!pending.empty()) {
        auto [row, column] = pending.front(); pending.pop();
        for (int direction = 0; direction < 4; ++direction) {
            int nr = row + dr[direction], nc = column + dc[direction];
            if (nr >= 0 && nr < n && nc >= 0 && nc < m && grid[nr][nc] == '0' && distance[nr][nc] < 0) {
                distance[nr][nc] = distance[row][column] + 1;
                pending.push({nr, nc});
            }
        }
    }
    cout << distance[tx][ty] << '\n';
}
""",
    "活动选择": r"""
#include <algorithm>
#include <climits>
#include <iostream>
#include <utility>
#include <vector>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<pair<long long, long long>> activities(n);
    for (auto &[end, start] : activities) cin >> start >> end;
    sort(activities.begin(), activities.end());
    long long last_end = LLONG_MIN;
    int answer = 0;
    for (auto [end, start] : activities) {
        if (start >= last_end) {
            ++answer;
            last_end = end;
        }
    }
    cout << answer << '\n';
}
""",
    "零一背包": r"""
#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;
int main() {
    int n, capacity;
    cin >> n >> capacity;
    vector<long long> best(capacity + 1);
    while (n--) {
        long long weight, value;
        cin >> weight >> value;
        if (weight > capacity) continue;
        for (int current = capacity; current >= weight; --current) {
            best[current] = max(best[current], best[current - weight] + value);
        }
    }
    cout << best[capacity] << '\n';
}
""",
    "Dijkstra 最短路": r"""
#include <functional>
#include <iostream>
#include <limits>
#include <queue>
#include <utility>
#include <vector>
using namespace std;
int main() {
    int n, m;
    cin >> n >> m;
    vector<vector<pair<int, long long>>> graph(n + 1);
    while (m--) {
        int from, to;
        long long weight;
        cin >> from >> to >> weight;
        graph[from].push_back({to, weight});
    }
    int source, target;
    cin >> source >> target;
    const long long infinity = numeric_limits<long long>::max();
    vector<long long> distance(n + 1, infinity);
    priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<pair<long long, int>>> pending;
    distance[source] = 0;
    pending.push({0, source});
    while (!pending.empty()) {
        auto [current_distance, vertex] = pending.top(); pending.pop();
        if (current_distance != distance[vertex]) continue;
        for (auto [next, weight] : graph[vertex]) {
            if (distance[next] > current_distance + weight) {
                distance[next] = current_distance + weight;
                pending.push({distance[next], next});
            }
        }
    }
    cout << (distance[target] == infinity ? -1 : distance[target]) << '\n';
}
""",
    "编辑距离": r"""
#include <algorithm>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
int main() {
    string source, target;
    cin >> source >> target;
    vector<int> previous(target.size() + 1), current(target.size() + 1);
    for (int j = 0; j <= int(target.size()); ++j) previous[j] = j;
    for (int i = 1; i <= int(source.size()); ++i) {
        current[0] = i;
        for (int j = 1; j <= int(target.size()); ++j) {
            current[j] = min({previous[j] + 1, current[j - 1] + 1,
                              previous[j - 1] + (source[i - 1] != target[j - 1])});
        }
        swap(previous, current);
    }
    cout << previous[target.size()] << '\n';
}
""",
    "N 皇后计数": r"""
#include <functional>
#include <iostream>
using namespace std;
int main() {
    int n;
    cin >> n;
    unsigned full = (1u << n) - 1;
    long long answer = 0;
    function<void(unsigned, unsigned, unsigned)> search = [&](unsigned columns, unsigned left, unsigned right) {
        if (columns == full) {
            ++answer;
            return;
        }
        unsigned available = full & ~(columns | left | right);
        while (available) {
            unsigned position = available & -available;
            available -= position;
            search(columns | position, ((left | position) << 1) & full, (right | position) >> 1);
        }
    };
    search(0, 0, 0);
    cout << answer << '\n';
}
""",
    "并查集连通性": r"""
#include <iostream>
#include <numeric>
#include <string>
#include <vector>
using namespace std;
struct DisjointSet {
    vector<int> parent, size;
    explicit DisjointSet(int n) : parent(n + 1), size(n + 1, 1) { iota(parent.begin(), parent.end(), 0); }
    int find(int value) { return parent[value] == value ? value : parent[value] = find(parent[value]); }
    void unite(int left, int right) {
        left = find(left); right = find(right);
        if (left == right) return;
        if (size[left] < size[right]) swap(left, right);
        parent[right] = left;
        size[left] += size[right];
    }
};
int main() {
    int n, q;
    cin >> n >> q;
    DisjointSet sets(n);
    while (q--) {
        string operation;
        int left, right;
        cin >> operation >> left >> right;
        if (operation == "UNION") sets.unite(left, right);
        else cout << (sets.find(left) == sets.find(right) ? "Yes" : "No") << '\n';
    }
}
""",
    "LRU 缓存模拟": r"""
#include <iostream>
#include <list>
#include <string>
#include <unordered_map>
#include <utility>
using namespace std;
int main() {
    int capacity, q;
    cin >> capacity >> q;
    list<pair<long long, long long>> recency;
    unordered_map<long long, list<pair<long long, long long>>::iterator> entries;
    while (q--) {
        string operation;
        long long key;
        cin >> operation >> key;
        auto found = entries.find(key);
        if (operation == "GET") {
            if (found == entries.end()) cout << -1 << '\n';
            else {
                recency.splice(recency.begin(), recency, found->second);
                cout << found->second->second << '\n';
            }
            continue;
        }
        long long value;
        cin >> value;
        if (found != entries.end()) {
            found->second->second = value;
            recency.splice(recency.begin(), recency, found->second);
        } else {
            recency.push_front({key, value});
            entries[key] = recency.begin();
            if (int(recency.size()) > capacity) {
                entries.erase(recency.back().first);
                recency.pop_back();
            }
        }
    }
}
""",
    "带括号表达式求值": r"""
#include <cctype>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
int precedence(char operation) { return operation == '+' || operation == '-' ? 1 : 2; }
void apply(vector<long long> &values, char operation) {
    long long right = values.back(); values.pop_back();
    long long left = values.back(); values.pop_back();
    if (operation == '+') values.push_back(left + right);
    else if (operation == '-') values.push_back(left - right);
    else if (operation == '*') values.push_back(left * right);
    else values.push_back(left / right);
}
int main() {
    string expression;
    cin >> expression;
    vector<long long> values;
    vector<char> operators;
    for (size_t index = 0; index < expression.size();) {
        if (isdigit(static_cast<unsigned char>(expression[index]))) {
            long long value = 0;
            while (index < expression.size() && isdigit(static_cast<unsigned char>(expression[index]))) {
                value = value * 10 + expression[index++] - '0';
            }
            values.push_back(value);
        } else if (expression[index] == '(') {
            operators.push_back(expression[index++]);
        } else if (expression[index] == ')') {
            while (operators.back() != '(') {
                char operation = operators.back(); operators.pop_back();
                apply(values, operation);
            }
            operators.pop_back();
            ++index;
        } else {
            char incoming = expression[index++];
            while (!operators.empty() && operators.back() != '(' && precedence(operators.back()) >= precedence(incoming)) {
                char operation = operators.back(); operators.pop_back();
                apply(values, operation);
            }
            operators.push_back(incoming);
        }
    }
    while (!operators.empty()) {
        char operation = operators.back(); operators.pop_back();
        apply(values, operation);
    }
    cout << values.back() << '\n';
}
""",
}
