#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "codegen.h"

/* Helper: case-insensitive substring search */
static int contains(const char* haystack, const char* needle) {
    if (!haystack || !needle) return 0;
    size_t hlen = strlen(haystack), nlen = strlen(needle);
    if (nlen > hlen) return 0;
    for (size_t i = 0; i <= hlen - nlen; i++) {
        size_t j;
        for (j = 0; j < nlen; j++) {
            if (tolower((unsigned char)haystack[i+j]) != tolower((unsigned char)needle[j]))
                break;
        }
        if (j == nlen) return 1;
    }
    return 0;
}

CodeLanguage codegen_detect_language(const char* request) {
    if (!request) return LANG_PYTHON;
    if (contains(request, "python") || contains(request, "py")) return LANG_PYTHON;
    if (contains(request, "c language") || contains(request, "in c") || contains(request, "c program")) return LANG_C;
    if (contains(request, "javascript") || contains(request, "js") || contains(request, "node")) return LANG_JAVASCRIPT;
    if (contains(request, "bash") || contains(request, "shell") || contains(request, "script")) return LANG_BASH;
    if (contains(request, "golang") || contains(request, "in go") || contains(request, " go ")) return LANG_GO;
    if (contains(request, "rust")) return LANG_RUST;
    return LANG_PYTHON;
}

const char* codegen_language_name(CodeLanguage lang) {
    switch (lang) {
        case LANG_PYTHON:     return "Python";
        case LANG_C:          return "C";
        case LANG_JAVASCRIPT: return "JavaScript";
        case LANG_BASH:       return "Bash";
        case LANG_GO:         return "Go";
        case LANG_RUST:       return "Rust";
        default:              return "Unknown";
    }
}

/* ===== TEMPLATES ===== */

/* Sort */
static const char* SORT_PY = "def sort_list(lst):\n    if len(lst) <= 1:\n        return lst\n    pivot = lst[len(lst) // 2]\n    left = [x for x in lst if x < pivot]\n    middle = [x for x in lst if x == pivot]\n    right = [x for x in lst if x > pivot]\n    return sort_list(left) + middle + sort_list(right)\n";
static const char* SORT_C = "#include <stdio.h>\n#include <stdlib.h>\n\nint compare(const void *a, const void *b) {\n    return (*(int*)a - *(int*)b);\n}\n\nvoid sort_array(int arr[], int n) {\n    qsort(arr, n, sizeof(int), compare);\n}\n\nint main() {\n    int arr[] = {5, 2, 8, 1, 9};\n    int n = sizeof(arr) / sizeof(arr[0]);\n    sort_array(arr, n);\n    for (int i = 0; i < n; i++) printf(\"%d \", arr[i]);\n    printf(\"\\n\");\n    return 0;\n}\n";
static const char* SORT_JS = "function sortList(arr) {\n    if (arr.length <= 1) return arr;\n    const pivot = arr[Math.floor(arr.length / 2)];\n    const left = arr.filter(x => x < pivot);\n    const middle = arr.filter(x => x === pivot);\n    const right = arr.filter(x => x > pivot);\n    return [...sortList(left), ...middle, ...sortList(right)];\n}\n";
static const char* SORT_BASH = "#!/bin/bash\nsort_array() {\n    echo \"$@\" | tr ' ' '\\n' | sort -n | tr '\\n' ' '\n    echo\n}\nsort_array 5 2 8 1 9\n";

/* Fibonacci */
static const char* FIB_PY = "def fibonacci(n):\n    if n <= 0:\n        return 0\n    elif n == 1:\n        return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n";
static const char* FIB_C = "#include <stdio.h>\n\nlong fibonacci(int n) {\n    if (n <= 0) return 0;\n    if (n == 1) return 1;\n    long a = 0, b = 1, temp;\n    for (int i = 2; i <= n; i++) {\n        temp = b;\n        b = a + b;\n        a = temp;\n    }\n    return b;\n}\n\nint main() {\n    for (int i = 0; i < 10; i++)\n        printf(\"fib(%d) = %ld\\n\", i, fibonacci(i));\n    return 0;\n}\n";
static const char* FIB_JS = "function fibonacci(n) {\n    if (n <= 0) return 0;\n    if (n === 1) return 1;\n    let a = 0, b = 1;\n    for (let i = 2; i <= n; i++) {\n        [a, b] = [b, a + b];\n    }\n    return b;\n}\n";
static const char* FIB_BASH = "#!/bin/bash\nfibonacci() {\n    local n=$1\n    if [ \"$n\" -le 0 ]; then echo 0; return; fi\n    if [ \"$n\" -eq 1 ]; then echo 1; return; fi\n    local a=0 b=1 temp\n    for ((i=2; i<=n; i++)); do\n        temp=$b; b=$((a+b)); a=$temp\n    done\n    echo $b\n}\nfibonacci 10\n";

/* Hello World */
static const char* HELLO_PY = "def hello_world():\n    print(\"Hello, World!\")\n\nhello_world()\n";
static const char* HELLO_C = "#include <stdio.h>\n\nint main() {\n    printf(\"Hello, World!\\n\");\n    return 0;\n}\n";
static const char* HELLO_JS = "function helloWorld() {\n    console.log(\"Hello, World!\");\n}\n\nhelloWorld();\n";
static const char* HELLO_BASH = "#!/bin/bash\necho 'Hello, World!'\n";

/* Factorial */
static const char* FACT_PY = "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n";
static const char* FACT_C = "#include <stdio.h>\n\nlong factorial(int n) {\n    if (n <= 1) return 1;\n    return n * factorial(n - 1);\n}\n\nint main() {\n    for (int i = 0; i <= 10; i++)\n        printf(\"%d! = %ld\\n\", i, factorial(i));\n    return 0;\n}\n";
static const char* FACT_JS = "function factorial(n) {\n    if (n <= 1) return 1;\n    return n * factorial(n - 1);\n}\n";
static const char* FACT_BASH = "#!/bin/bash\nfactorial() {\n    local n=$1\n    if [ \"$n\" -le 1 ]; then echo 1; return; fi\n    local sub=$(factorial $((n-1)))\n    echo $((n * sub))\n}\nfactorial 10\n";

/* Reverse */
static const char* REV_PY = "def reverse_list(lst):\n    return lst[::-1]\n\ndef reverse_string(s):\n    return s[::-1]\n";
static const char* REV_C = "#include <stdio.h>\n#include <string.h>\n\nvoid reverse_string(char* str) {\n    int len = strlen(str);\n    for (int i = 0; i < len / 2; i++) {\n        char tmp = str[i];\n        str[i] = str[len-1-i];\n        str[len-1-i] = tmp;\n    }\n}\n\nint main() {\n    char s[] = \"Hello\";\n    reverse_string(s);\n    printf(\"%s\\n\", s);\n    return 0;\n}\n";
static const char* REV_JS = "function reverse(arr) {\n    return [...arr].reverse();\n}\n\nfunction reverseString(str) {\n    return str.split('').reverse().join('');\n}\n";
static const char* REV_BASH = "#!/bin/bash\nreverse_string() {\n    echo \"$1\" | rev\n}\nreverse_string \"Hello World\"\n";

/* Read File */
static const char* READF_PY = "def read_file(filename):\n    with open(filename, 'r') as f:\n        return f.read()\n";
static const char* READF_C = "#include <stdio.h>\n#include <stdlib.h>\n\nchar* read_file(const char* filename) {\n    FILE* f = fopen(filename, \"r\");\n    if (!f) return NULL;\n    fseek(f, 0, SEEK_END);\n    long len = ftell(f);\n    fseek(f, 0, SEEK_SET);\n    char* buf = malloc(len + 1);\n    if (buf) { fread(buf, 1, len, f); buf[len] = '\\0'; }\n    fclose(f);\n    return buf;\n}\n\nint main() {\n    char* content = read_file(\"test.txt\");\n    if (content) { printf(\"%s\", content); free(content); }\n    return 0;\n}\n";
static const char* READF_JS = "const fs = require('fs');\n\nfunction readFile(filename) {\n    return fs.readFileSync(filename, 'utf8');\n}\n";
static const char* READF_BASH = "#!/bin/bash\nread_file() {\n    cat \"$1\"\n}\nread_file \"$1\"\n";

/* HTTP Server */
static const char* HTTP_PY = "from http.server import HTTPServer, BaseHTTPRequestHandler\n\nclass Handler(BaseHTTPRequestHandler):\n    def do_GET(self):\n        self.send_response(200)\n        self.send_header('Content-Type', 'text/html')\n        self.end_headers()\n        self.wfile.write(b'<h1>Hello, World!</h1>')\n\nserver = HTTPServer(('localhost', 8080), Handler)\nprint('Server running on http://localhost:8080')\nserver.serve_forever()\n";
static const char* HTTP_C = "#include <stdio.h>\n#include <string.h>\n#include <sys/socket.h>\n#include <netinet/in.h>\n#include <unistd.h>\n\nint main() {\n    int server_fd = socket(AF_INET, SOCK_STREAM, 0);\n    struct sockaddr_in addr = {AF_INET, htons(8080), {INADDR_ANY}};\n    bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));\n    listen(server_fd, 5);\n    printf(\"Server on port 8080\\n\");\n    while (1) {\n        int client = accept(server_fd, NULL, NULL);\n        const char* resp = \"HTTP/1.1 200 OK\\r\\nContent-Length: 13\\r\\n\\r\\nHello, World!\";\n        write(client, resp, strlen(resp));\n        close(client);\n    }\n    return 0;\n}\n";
static const char* HTTP_JS = "const http = require('http');\n\nconst server = http.createServer((req, res) => {\n    res.writeHead(200, {'Content-Type': 'text/html'});\n    res.end('<h1>Hello, World!</h1>');\n});\n\nserver.listen(8080, () => {\n    console.log('Server running on http://localhost:8080');\n});\n";
static const char* HTTP_BASH = "#!/bin/bash\nwhile true; do\n    echo -e \"HTTP/1.1 200 OK\\r\\nContent-Length: 13\\r\\n\\r\\nHello, World!\" | nc -l -p 8080 -q 1\ndone\n";

/* FizzBuzz */
static const char* FIZZ_PY = "def fizzbuzz(n):\n    for i in range(1, n + 1):\n        if i % 15 == 0:\n            print('FizzBuzz')\n        elif i % 3 == 0:\n            print('Fizz')\n        elif i % 5 == 0:\n            print('Buzz')\n        else:\n            print(i)\n\nfizzbuzz(100)\n";
static const char* FIZZ_C = "#include <stdio.h>\n\nint main() {\n    for (int i = 1; i <= 100; i++) {\n        if (i % 15 == 0) printf(\"FizzBuzz\\n\");\n        else if (i % 3 == 0) printf(\"Fizz\\n\");\n        else if (i % 5 == 0) printf(\"Buzz\\n\");\n        else printf(\"%d\\n\", i);\n    }\n    return 0;\n}\n";
static const char* FIZZ_JS = "function fizzbuzz(n) {\n    for (let i = 1; i <= n; i++) {\n        if (i % 15 === 0) console.log('FizzBuzz');\n        else if (i % 3 === 0) console.log('Fizz');\n        else if (i % 5 === 0) console.log('Buzz');\n        else console.log(i);\n    }\n}\n\nfizzbuzz(100);\n";
static const char* FIZZ_BASH = "#!/bin/bash\nfor ((i=1; i<=100; i++)); do\n    if ((i % 15 == 0)); then echo 'FizzBuzz'\n    elif ((i % 3 == 0)); then echo 'Fizz'\n    elif ((i % 5 == 0)); then echo 'Buzz'\n    else echo $i\n    fi\ndone\n";

/* Binary Search */
static const char* BSEARCH_PY = "def binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n";
static const char* BSEARCH_C = "#include <stdio.h>\n\nint binary_search(int arr[], int n, int target) {\n    int low = 0, high = n - 1;\n    while (low <= high) {\n        int mid = (low + high) / 2;\n        if (arr[mid] == target) return mid;\n        else if (arr[mid] < target) low = mid + 1;\n        else high = mid - 1;\n    }\n    return -1;\n}\n\nint main() {\n    int arr[] = {1,3,5,7,9,11,13};\n    int idx = binary_search(arr, 7, 7);\n    printf(\"Found at index: %d\\n\", idx);\n    return 0;\n}\n";
static const char* BSEARCH_JS = "function binarySearch(arr, target) {\n    let low = 0, high = arr.length - 1;\n    while (low <= high) {\n        const mid = Math.floor((low + high) / 2);\n        if (arr[mid] === target) return mid;\n        else if (arr[mid] < target) low = mid + 1;\n        else high = mid - 1;\n    }\n    return -1;\n}\n";
static const char* BSEARCH_BASH = "#!/bin/bash\nbinary_search() {\n    local -a arr=(\"$@\")\n    local target=${arr[-1]}\n    unset 'arr[-1]'\n    local low=0 high=$((${#arr[@]}-1))\n    while [ $low -le $high ]; do\n        local mid=$(( (low+high)/2 ))\n        if [ ${arr[$mid]} -eq $target ]; then echo $mid; return; fi\n        if [ ${arr[$mid]} -lt $target ]; then low=$((mid+1)); else high=$((mid-1)); fi\n    done\n    echo -1\n}\nbinary_search 1 3 5 7 9 11 13 7\n";

/* Linked List */
static const char* LLIST_PY = "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\nclass LinkedList:\n    def __init__(self):\n        self.head = None\n\n    def append(self, data):\n        node = Node(data)\n        if not self.head:\n            self.head = node\n            return\n        curr = self.head\n        while curr.next:\n            curr = curr.next\n        curr.next = node\n\n    def display(self):\n        curr = self.head\n        while curr:\n            print(curr.data, end=' -> ')\n            curr = curr.next\n        print('None')\n";
static const char* LLIST_C = "#include <stdio.h>\n#include <stdlib.h>\n\ntypedef struct Node {\n    int data;\n    struct Node* next;\n} Node;\n\nNode* create_node(int data) {\n    Node* n = malloc(sizeof(Node));\n    n->data = data;\n    n->next = NULL;\n    return n;\n}\n\nvoid append(Node** head, int data) {\n    Node* n = create_node(data);\n    if (!*head) { *head = n; return; }\n    Node* curr = *head;\n    while (curr->next) curr = curr->next;\n    curr->next = n;\n}\n\nvoid display(Node* head) {\n    while (head) { printf(\"%d -> \", head->data); head = head->next; }\n    printf(\"NULL\\n\");\n}\n\nint main() {\n    Node* list = NULL;\n    append(&list, 1); append(&list, 2); append(&list, 3);\n    display(list);\n    return 0;\n}\n";
static const char* LLIST_JS = "class Node {\n    constructor(data) {\n        this.data = data;\n        this.next = null;\n    }\n}\n\nclass LinkedList {\n    constructor() { this.head = null; }\n\n    append(data) {\n        const node = new Node(data);\n        if (!this.head) { this.head = node; return; }\n        let curr = this.head;\n        while (curr.next) curr = curr.next;\n        curr.next = node;\n    }\n\n    display() {\n        let curr = this.head, result = '';\n        while (curr) { result += curr.data + ' -> '; curr = curr.next; }\n        console.log(result + 'null');\n    }\n}\n";
static const char* LLIST_BASH = "#!/bin/bash\ndeclare -a list_data\nlist_append() { list_data+=(\"$1\"); }\nlist_display() {\n    for item in \"${list_data[@]}\"; do printf '%s -> ' \"$item\"; done\n    echo 'NULL'\n}\nlist_append 1; list_append 2; list_append 3\nlist_display\n";

/* Stub template */
static const char* STUB_PY = "# TODO: Implement requested functionality\ndef stub():\n    pass\n";
static const char* STUB_C = "#include <stdio.h>\n\n/* TODO: Implement requested functionality */\nint main() {\n    printf(\"Not implemented yet\\n\");\n    return 0;\n}\n";
static const char* STUB_JS = "// TODO: Implement requested functionality\nfunction stub() {\n    console.log('Not implemented yet');\n}\n";
static const char* STUB_BASH = "#!/bin/bash\n# TODO: Implement requested functionality\necho 'Not implemented yet'\n";

/* Task detection enum */
typedef enum {
    TASK_SORT, TASK_REVERSE, TASK_FIBONACCI, TASK_FACTORIAL,
    TASK_HELLO, TASK_READFILE, TASK_HTTP, TASK_FIZZBUZZ,
    TASK_BSEARCH, TASK_LLIST, TASK_UNKNOWN
} TaskType;

static TaskType detect_task(const char* request) {
    if (contains(request, "sort"))                           return TASK_SORT;
    if (contains(request, "reverse"))                       return TASK_REVERSE;
    if (contains(request, "fibonacci") || contains(request, "fib")) return TASK_FIBONACCI;
    if (contains(request, "factorial"))                     return TASK_FACTORIAL;
    if (contains(request, "hello world") || contains(request, "hello"))  return TASK_HELLO;
    if (contains(request, "read file"))                     return TASK_READFILE;
    if (contains(request, "http") || contains(request, "server") || contains(request, "web")) return TASK_HTTP;
    if (contains(request, "fizzbuzz"))                      return TASK_FIZZBUZZ;
    if (contains(request, "binary search"))                 return TASK_BSEARCH;
    if (contains(request, "linked list"))                   return TASK_LLIST;
    return TASK_UNKNOWN;
}

static const char* get_template(TaskType task, CodeLanguage lang) {
    switch (task) {
        case TASK_SORT:      return (lang==LANG_C)?SORT_C:(lang==LANG_JAVASCRIPT)?SORT_JS:(lang==LANG_BASH)?SORT_BASH:SORT_PY;
        case TASK_REVERSE:   return (lang==LANG_C)?REV_C:(lang==LANG_JAVASCRIPT)?REV_JS:(lang==LANG_BASH)?REV_BASH:REV_PY;
        case TASK_FIBONACCI: return (lang==LANG_C)?FIB_C:(lang==LANG_JAVASCRIPT)?FIB_JS:(lang==LANG_BASH)?FIB_BASH:FIB_PY;
        case TASK_FACTORIAL: return (lang==LANG_C)?FACT_C:(lang==LANG_JAVASCRIPT)?FACT_JS:(lang==LANG_BASH)?FACT_BASH:FACT_PY;
        case TASK_HELLO:     return (lang==LANG_C)?HELLO_C:(lang==LANG_JAVASCRIPT)?HELLO_JS:(lang==LANG_BASH)?HELLO_BASH:HELLO_PY;
        case TASK_READFILE:  return (lang==LANG_C)?READF_C:(lang==LANG_JAVASCRIPT)?READF_JS:(lang==LANG_BASH)?READF_BASH:READF_PY;
        case TASK_HTTP:      return (lang==LANG_C)?HTTP_C:(lang==LANG_JAVASCRIPT)?HTTP_JS:(lang==LANG_BASH)?HTTP_BASH:HTTP_PY;
        case TASK_FIZZBUZZ:  return (lang==LANG_C)?FIZZ_C:(lang==LANG_JAVASCRIPT)?FIZZ_JS:(lang==LANG_BASH)?FIZZ_BASH:FIZZ_PY;
        case TASK_BSEARCH:   return (lang==LANG_C)?BSEARCH_C:(lang==LANG_JAVASCRIPT)?BSEARCH_JS:(lang==LANG_BASH)?BSEARCH_BASH:BSEARCH_PY;
        case TASK_LLIST:     return (lang==LANG_C)?LLIST_C:(lang==LANG_JAVASCRIPT)?LLIST_JS:(lang==LANG_BASH)?LLIST_BASH:LLIST_PY;
        default:             return (lang==LANG_C)?STUB_C:(lang==LANG_JAVASCRIPT)?STUB_JS:(lang==LANG_BASH)?STUB_BASH:STUB_PY;
    }
}

static const char* get_explanation(TaskType task) {
    switch (task) {
        case TASK_SORT:      return "Sorts a collection using an efficient algorithm";
        case TASK_REVERSE:   return "Reverses a string or list in place";
        case TASK_FIBONACCI: return "Computes the nth Fibonacci number iteratively";
        case TASK_FACTORIAL: return "Computes factorial using recursion";
        case TASK_HELLO:     return "Prints Hello World to stdout";
        case TASK_READFILE:  return "Reads entire file contents into memory";
        case TASK_HTTP:      return "Creates a basic HTTP server on port 8080";
        case TASK_FIZZBUZZ:  return "Prints FizzBuzz sequence from 1 to 100";
        case TASK_BSEARCH:   return "Binary search on a sorted array, returns index or -1";
        case TASK_LLIST:     return "Singly linked list with append and display operations";
        default:             return "Stub function - task not recognized";
    }
}

int codegen_generate(const char* request, CodeLanguage lang, CodeResult* result) {
    if (!request || !result) return -1;

    memset(result, 0, sizeof(CodeResult));
    result->language = lang;

    TaskType task = detect_task(request);
    const char* tmpl = get_template(task, lang);

    strncpy(result->code, tmpl, sizeof(result->code) - 1);
    result->code[sizeof(result->code) - 1] = '\0';

    strncpy(result->explanation, get_explanation(task), sizeof(result->explanation) - 1);
    result->explanation[sizeof(result->explanation) - 1] = '\0';

    result->confidence = (task == TASK_UNKNOWN) ? 20 : 85;

    return 0;
}
