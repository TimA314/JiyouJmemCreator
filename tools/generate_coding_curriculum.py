#!/usr/bin/env python3
"""
Generate comprehensive coding curriculum using Grok API.

Creates coding.jcur with 32,000+ items covering:
- Web Frontend (HTML, CSS, JavaScript, TypeScript)
- Backend Languages (Python, C, C++, C#, Go, Rust)
- Frameworks (React, Vue, Angular, Node, Django, etc.)
- Data & Databases (SQL, NoSQL, ORMs)
- CS Fundamentals (Data Structures, Algorithms, Design Patterns)
- Tools & Practices (Git, Testing, DevOps, Security)

Usage:
    export GROK_API_KEY="your-key-here"
    python tools/generate_coding_curriculum.py --all
    python tools/generate_coding_curriculum.py --category python_core --count 100
    python tools/generate_coding_curriculum.py --list-categories
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional


# =============================================================================
# GROK API CLIENT
# =============================================================================

GROK_API_KEY: Optional[str] = None

def get_api_key() -> str:
    """Get Grok API key from environment or file."""
    global GROK_API_KEY
    if GROK_API_KEY:
        return GROK_API_KEY

    api_key = os.environ.get("GROK_API_KEY")
    if not api_key:
        key_file = Path.home() / ".grok_api_key"
        if key_file.exists():
            api_key = key_file.read_text().strip()
        else:
            print("Error: GROK_API_KEY environment variable not set")
            print("Set it with: export GROK_API_KEY='your-key-here'")
            print("Or create ~/.grok_api_key file with your key")
            sys.exit(1)

    GROK_API_KEY = api_key
    return api_key


def call_grok_api(messages: List[Dict], temperature: float = 0.9, max_tokens: int = 4000) -> str:
    """Call Grok API directly using urllib."""
    api_key = get_api_key()

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "curl/8.0",
        "Accept": "application/json",
    }
    data = {
        "model": "grok-4-1-fast-non-reasoning",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        raise Exception(f"Grok API error {e.code}: {error_body}")
    except urllib.error.URLError as e:
        raise Exception(f"Network error: {e.reason}")


# =============================================================================
# CODING CURRICULUM CATEGORIES
# =============================================================================

CATEGORIES = {
    # =========================================================================
    # TIER 1: WEB FRONTEND (~7,000 items)
    # =========================================================================

    "html_fundamentals": {
        "count": 800,
        "description": "HTML5 tags, attributes, semantic markup, forms, accessibility",
        "prompt": """Generate dialogue pairs teaching HTML fundamentals.

The SOURCE is a question about HTML, TARGET is JiYou's clear explanation.

Include varied topics:
- Document structure: <!DOCTYPE>, <html>, <head>, <body>, <meta>
- Text elements: <h1>-<h6>, <p>, <span>, <div>, <br>, <hr>
- Semantic HTML5: <header>, <nav>, <main>, <article>, <section>, <aside>, <footer>
- Lists: <ul>, <ol>, <li>, <dl>, <dt>, <dd>
- Links and images: <a href>, <img src alt>, <figure>, <figcaption>
- Tables: <table>, <tr>, <td>, <th>, <thead>, <tbody>, <tfoot>
- Forms: <form>, <input>, <textarea>, <select>, <button>, <label>
- Input types: text, email, password, number, date, checkbox, radio, file
- Form attributes: required, placeholder, pattern, min, max, disabled
- Media: <video>, <audio>, <source>, <iframe>, <canvas>, <svg>
- Accessibility: alt text, aria-*, role, tabindex, screen readers
- Global attributes: id, class, style, data-*, title, lang

Mix of:
- "What is the X tag used for?" → explanation
- "How do I create X in HTML?" → code example
- "What's the difference between X and Y?" → comparison
- Code snippet → "This HTML does X because..."

JiYou should give practical examples with proper HTML syntax.""",
    },

    "css_fundamentals": {
        "count": 1000,
        "description": "CSS selectors, box model, flexbox, grid, animations, responsive design",
        "prompt": """Generate dialogue pairs teaching CSS fundamentals.

The SOURCE is a question about CSS, TARGET is JiYou's explanation with examples.

Include varied topics:
- Selectors: element, class, id, attribute, pseudo-class, pseudo-element
- Combinators: descendant, child (>), sibling (+, ~)
- Specificity and cascade, !important
- Box model: margin, padding, border, width, height, box-sizing
- Display: block, inline, inline-block, none, flex, grid
- Positioning: static, relative, absolute, fixed, sticky, z-index
- Flexbox: display:flex, justify-content, align-items, flex-direction, flex-wrap, gap
- Grid: display:grid, grid-template-columns/rows, grid-gap, grid-area, fr units
- Typography: font-family, font-size, font-weight, line-height, text-align, text-decoration
- Colors: hex, rgb, rgba, hsl, hsla, named colors, opacity
- Backgrounds: background-color, background-image, gradient, background-size
- Borders: border, border-radius, box-shadow
- Transitions: transition property, duration, timing-function
- Animations: @keyframes, animation property
- Transforms: translate, rotate, scale, skew
- Media queries: @media, breakpoints, responsive design
- CSS variables: --custom-property, var()
- Units: px, em, rem, %, vh, vw, fr

Mix of:
- "How do I center X?" → flexbox/grid solution
- "What does X property do?" → explanation
- Code snippet → "This CSS achieves X by..."
- "Why isn't my X working?" → common CSS issues

JiYou should provide practical, copy-paste ready CSS examples.""",
    },

    "javascript_core": {
        "count": 1200,
        "description": "JavaScript syntax, DOM manipulation, events, ES6+, async programming",
        "prompt": """Generate dialogue pairs teaching JavaScript programming.

The SOURCE is a question or code snippet, TARGET is JiYou's explanation.

Include varied topics:
- Variables: let, const, var, hoisting, scope
- Data types: string, number, boolean, null, undefined, symbol, bigint
- Operators: arithmetic, comparison, logical, ternary, nullish coalescing (??)
- Strings: template literals, methods (slice, split, join, includes, replace)
- Arrays: methods (map, filter, reduce, forEach, find, some, every, sort)
- Objects: literals, destructuring, spread operator, Object methods
- Functions: declaration, expression, arrow functions, default params, rest params
- Control flow: if/else, switch, for, while, for...of, for...in
- ES6+: let/const, arrow functions, destructuring, spread/rest, modules
- Classes: constructor, methods, inheritance, static, getters/setters
- Promises: new Promise, then, catch, finally, Promise.all, Promise.race
- Async/await: async functions, await, error handling with try/catch
- DOM: document.querySelector, getElementById, createElement, appendChild
- Events: addEventListener, event object, bubbling, delegation
- Fetch API: fetch(), Response, JSON parsing, error handling
- Local Storage: setItem, getItem, removeItem, JSON stringify/parse
- Error handling: try/catch/finally, throw, Error types
- Modules: import, export, default exports, named exports
- Common patterns: debounce, throttle, memoization, closure
- Array/Object manipulation: deep copy, merge, filter unique

Mix of:
- "How do I X in JavaScript?" → code example
- "What does X do?" → explanation
- Code snippet → "This code X because..."
- "Why is this throwing an error?" → debugging explanation

JiYou should provide modern ES6+ JavaScript examples.""",
    },

    "typescript_basics": {
        "count": 1000,
        "description": "TypeScript types, interfaces, generics, type guards",
        "prompt": """Generate dialogue pairs teaching TypeScript.

The SOURCE is a question about TypeScript, TARGET is JiYou's explanation.

Include varied topics:
- Basic types: string, number, boolean, array, tuple, enum, any, unknown, void, never
- Type annotations: variable types, function parameters, return types
- Interfaces: defining shape of objects, optional properties, readonly
- Type aliases: type keyword, union types, intersection types
- Generics: generic functions, generic interfaces, generic classes, constraints
- Type guards: typeof, instanceof, in operator, custom type guards
- Utility types: Partial, Required, Pick, Omit, Record, Exclude, Extract
- Classes with types: access modifiers (public, private, protected)
- Function overloads
- Type assertions: as keyword, angle bracket syntax
- Literal types, template literal types
- Discriminated unions, exhaustive checking
- Type inference, contextual typing
- Strict mode options: strictNullChecks, noImplicitAny
- Declaration files (.d.ts), @types packages
- Migrating from JavaScript to TypeScript

Mix of:
- "How do I type X?" → code example with types
- "What's the difference between X and Y?" → type comparison
- "Why is TypeScript complaining about X?" → type error explanation
- Code snippet → "This type does X because..."

JiYou should show both the TypeScript code and explain the types.""",
    },

    # =========================================================================
    # TIER 2: BACKEND LANGUAGES (~8,000 items)
    # =========================================================================

    "python_core": {
        "count": 1200,
        "description": "Python syntax, data structures, OOP, standard library",
        "prompt": """Generate dialogue pairs teaching Python programming.

The SOURCE is a question or code snippet, TARGET is JiYou's explanation.

Include varied topics:
- Basic syntax: variables, operators, indentation, comments
- Data types: int, float, str, bool, None
- Strings: f-strings, methods, slicing, formatting
- Lists: indexing, slicing, methods (append, extend, pop, sort)
- Tuples: immutability, unpacking, named tuples
- Dictionaries: keys, values, items, get, setdefault, comprehensions
- Sets: union, intersection, difference, add, remove
- Control flow: if/elif/else, for, while, break, continue, pass
- Functions: def, return, *args, **kwargs, default values, lambda
- List comprehensions, dict comprehensions, generator expressions
- Classes: __init__, self, inheritance, super(), @property
- Magic methods: __str__, __repr__, __len__, __eq__, __iter__
- Decorators: @staticmethod, @classmethod, custom decorators
- Context managers: with statement, __enter__, __exit__
- Exception handling: try/except/finally, raise, custom exceptions
- File I/O: open(), read(), write(), with statement, modes
- Modules: import, from...import, __name__, __main__
- Standard library: os, sys, json, datetime, collections, itertools, functools
- Type hints: annotations, Optional, List, Dict, Union, typing module
- Virtual environments: venv, pip, requirements.txt

Mix of:
- "How do I X in Python?" → code example
- "What does X do?" → explanation
- Code snippet → "This Python code does X because..."
- "What's the Pythonic way to X?" → best practices

JiYou should provide clean, PEP 8 compliant Python code.""",
    },

    "c_programming": {
        "count": 800,
        "description": "C syntax, pointers, memory management, data structures",
        "prompt": """Generate dialogue pairs teaching C programming.

The SOURCE is a question about C, TARGET is JiYou's explanation.

Include varied topics:
- Basic syntax: main(), printf, scanf, data types
- Data types: int, char, float, double, long, short, unsigned
- Variables and constants: declaration, initialization, #define, const
- Operators: arithmetic, relational, logical, bitwise, assignment
- Control flow: if/else, switch, for, while, do-while, break, continue
- Functions: declaration, definition, parameters, return values
- Pointers: *, &, pointer arithmetic, NULL, void pointers
- Arrays: declaration, initialization, multidimensional, passing to functions
- Strings: char arrays, string.h functions (strlen, strcpy, strcmp, strcat)
- Structs: definition, accessing members, pointers to structs, typedef
- Unions and enums
- Dynamic memory: malloc, calloc, realloc, free, memory leaks
- File I/O: fopen, fclose, fread, fwrite, fprintf, fscanf
- Preprocessor: #include, #define, #ifdef, #ifndef, macros
- Header files: creating and using .h files
- Compilation: gcc, object files, linking
- Common patterns: linked lists, stacks, queues in C
- Debugging: common errors, segfaults, valgrind
- Memory layout: stack vs heap, buffer overflows

Mix of:
- "How do I X in C?" → code example
- "What does X do?" → explanation
- Code snippet → "This C code does X because..."
- "Why does this crash?" → memory/pointer explanation

JiYou should explain low-level concepts clearly with examples.""",
    },

    "cpp_programming": {
        "count": 1000,
        "description": "C++ OOP, STL, templates, modern C++17/20",
        "prompt": """Generate dialogue pairs teaching C++ programming.

The SOURCE is a question about C++, TARGET is JiYou's explanation.

Include varied topics:
- C++ vs C: additional features, namespaces, std::
- Classes: public/private/protected, constructors, destructors
- OOP: inheritance, polymorphism, virtual functions, abstract classes
- References vs pointers, const correctness
- Operator overloading
- Templates: function templates, class templates, template specialization
- STL containers: vector, list, deque, map, set, unordered_map
- STL algorithms: sort, find, transform, accumulate, for_each
- Iterators: begin, end, iterator types
- Smart pointers: unique_ptr, shared_ptr, weak_ptr (no raw new/delete)
- RAII: Resource Acquisition Is Initialization
- Move semantics: rvalue references, std::move, move constructors
- Lambda expressions: capture, parameters, return type
- Modern C++11/14/17/20: auto, range-based for, constexpr, if constexpr
- Exception handling: try/catch, throw, exception classes
- Namespaces and using declarations
- Header and source file organization
- Copy constructor, copy assignment, rule of three/five
- Strings: std::string, string_view (C++17)
- File I/O: fstream, ifstream, ofstream

Mix of:
- "How do I X in C++?" → modern C++ solution
- "What's the difference between X and Y?" → comparison
- Code snippet → "This C++ code does X because..."
- "What's wrong with this code?" → common C++ mistakes

JiYou should promote modern C++ best practices (smart pointers, RAII).""",
    },

    "csharp_dotnet": {
        "count": 800,
        "description": "C# and .NET, LINQ, async, generics",
        "prompt": """Generate dialogue pairs teaching C# and .NET.

The SOURCE is a question about C#, TARGET is JiYou's explanation.

Include varied topics:
- Basic syntax: Main, Console.WriteLine, variables, operators
- Data types: int, string, bool, double, decimal, var
- Strings: interpolation, verbatim, StringBuilder
- Collections: List<T>, Dictionary<K,V>, HashSet<T>, arrays
- Control flow: if/else, switch (with patterns), for, foreach, while
- Classes: properties, auto-properties, constructors, inheritance
- Access modifiers: public, private, protected, internal
- Interfaces and abstract classes
- Generics: generic classes, methods, constraints
- LINQ: from, where, select, orderby, join, method syntax
- Lambda expressions and delegates
- Events and event handlers
- Async/await: Task, Task<T>, async methods, ConfigureAwait
- Exception handling: try/catch/finally, throw, custom exceptions
- Nullable types: int?, Nullable<T>, null-coalescing (??)
- Pattern matching: is, switch expressions
- Records (C# 9+), init-only properties
- Extension methods
- File I/O: File class, StreamReader/Writer
- Attributes and reflection basics

Mix of:
- "How do I X in C#?" → code example
- "What does X do?" → explanation
- LINQ query → "This query does X"
- "What's the difference between X and Y?" → comparison

JiYou should show modern C# (8.0+) patterns and practices.""",
    },

    "go_basics": {
        "count": 500,
        "description": "Go syntax, goroutines, channels, interfaces",
        "prompt": """Generate dialogue pairs teaching Go programming.

The SOURCE is a question about Go, TARGET is JiYou's explanation.

Include varied topics:
- Basic syntax: package main, func main, fmt.Println
- Variables: var, :=, constants, type inference
- Data types: int, string, bool, float64, rune, byte
- Arrays and slices: make, append, len, cap, slicing
- Maps: make, access, delete, comma ok idiom
- Structs: definition, methods, embedding
- Pointers: *, &, pointer receivers vs value receivers
- Functions: multiple return values, named returns, defer
- Error handling: error interface, errors.New, fmt.Errorf
- Interfaces: implicit implementation, empty interface
- Goroutines: go keyword, concurrent execution
- Channels: make(chan), send, receive, buffered channels
- Select statement for channel operations
- sync package: WaitGroup, Mutex
- Packages and imports, exported names (capitalization)
- Testing: testing package, go test, table-driven tests
- Common patterns: worker pools, fan-out/fan-in

Mix of:
- "How do I X in Go?" → idiomatic Go solution
- "What's the Go way to X?" → best practices
- Code snippet → "This Go code does X because..."
- Concurrency pattern → explanation

JiYou should show idiomatic Go with proper error handling.""",
    },

    # =========================================================================
    # TIER 3: FRAMEWORKS (~6,000 items)
    # =========================================================================

    "react_fundamentals": {
        "count": 800,
        "description": "React components, hooks, state management, patterns",
        "prompt": """Generate dialogue pairs teaching React.

The SOURCE is a question about React, TARGET is JiYou's explanation.

Include varied topics:
- Components: functional components, JSX syntax, props
- Hooks: useState, useEffect, useContext, useRef, useCallback, useMemo
- State management: lifting state up, prop drilling, context
- useEffect: dependencies array, cleanup functions, common patterns
- Event handling: onClick, onChange, onSubmit, event object
- Forms: controlled components, form state, validation
- Conditional rendering: ternary, &&, early returns
- Lists and keys: map, key prop importance
- Custom hooks: creating reusable logic
- Component composition: children prop, render props
- Performance: React.memo, useCallback, useMemo, when to use
- Refs: useRef for DOM access, forwarding refs
- Error boundaries, Suspense, lazy loading
- React Router: Routes, Route, Link, useNavigate, useParams
- State management: useReducer, context patterns, external stores
- TypeScript with React: FC type, props interfaces
- Common patterns: container/presentational, compound components
- Styling: CSS modules, styled-components, inline styles
- Testing: React Testing Library basics

Mix of:
- "How do I X in React?" → code example with hooks
- "When should I use X vs Y?" → use case explanation
- Code snippet → "This React code does X because..."
- "Why is my component re-rendering?" → performance explanation

JiYou should show modern React (hooks, functional components).""",
    },

    "vue_fundamentals": {
        "count": 800,
        "description": "Vue 3 Composition API, reactivity, components",
        "prompt": """Generate dialogue pairs teaching Vue.js.

The SOURCE is a question about Vue, TARGET is JiYou's explanation.

Include varied topics:
- Vue 3 setup: createApp, mounting, Single File Components (.vue)
- Template syntax: interpolation, directives (v-if, v-for, v-bind, v-on)
- Composition API: setup(), ref, reactive, computed, watch
- Component props: defineProps, prop validation
- Component events: defineEmits, $emit
- Lifecycle hooks: onMounted, onUpdated, onUnmounted
- Reactivity: ref vs reactive, toRefs, readonly
- Computed properties and watchers
- v-model: two-way binding, custom v-model
- Slots: default, named, scoped slots
- Provide/inject for dependency injection
- Vue Router: router-view, router-link, useRouter, useRoute
- Pinia (state management): defineStore, state, getters, actions
- Composables: creating reusable logic
- Template refs: ref attribute, accessing DOM
- Transition and animation
- TypeScript with Vue 3

Mix of:
- "How do I X in Vue?" → Composition API example
- "What's the difference between Options API and Composition API?" → comparison
- Code snippet → "This Vue code does X because..."
- "How do I share state between components?" → state management

JiYou should show Vue 3 Composition API patterns.""",
    },

    "angular_fundamentals": {
        "count": 700,
        "description": "Angular components, services, RxJS, routing",
        "prompt": """Generate dialogue pairs teaching Angular.

The SOURCE is a question about Angular, TARGET is JiYou's explanation.

Include varied topics:
- Angular CLI: ng new, ng generate, ng serve
- Components: @Component decorator, template, styles
- Modules: @NgModule, declarations, imports, providers
- Templates: interpolation, property binding [], event binding ()
- Directives: *ngIf, *ngFor, ngClass, ngStyle
- Two-way binding: [(ngModel)], FormsModule
- Services: @Injectable, dependency injection
- HTTP: HttpClient, observables, error handling
- RxJS basics: Observable, subscribe, pipe, operators (map, filter, switchMap)
- Routing: RouterModule, Routes, routerLink, ActivatedRoute
- Route guards: CanActivate, resolvers
- Reactive Forms: FormGroup, FormControl, validators
- Pipes: built-in pipes, custom pipes
- Component communication: @Input, @Output, EventEmitter
- Lifecycle hooks: ngOnInit, ngOnChanges, ngOnDestroy
- ViewChild and ContentChild
- Angular signals (newer versions)

Mix of:
- "How do I X in Angular?" → code example
- "What's the difference between X and Y?" → comparison
- "How does dependency injection work?" → explanation
- Code snippet → "This Angular code does X because..."

JiYou should show Angular best practices with TypeScript.""",
    },

    "nodejs_express": {
        "count": 600,
        "description": "Node.js runtime, Express.js, async patterns",
        "prompt": """Generate dialogue pairs teaching Node.js and Express.

The SOURCE is a question about Node/Express, TARGET is JiYou's explanation.

Include varied topics:
- Node.js basics: running scripts, npm, package.json
- CommonJS vs ES Modules: require vs import
- npm: install, --save-dev, scripts, npx
- Built-in modules: fs, path, http, os, process
- Event loop and async nature of Node.js
- Callbacks, Promises, async/await in Node
- Express setup: express(), app.listen, basic server
- Routing: app.get, app.post, app.put, app.delete
- Route parameters: req.params, req.query, req.body
- Middleware: app.use, next(), order matters
- Built-in middleware: express.json(), express.static()
- Error handling middleware: error-first pattern
- Request/response: req object, res.send, res.json, res.status
- Router: express.Router(), modular routes
- Template engines: EJS, Pug basics
- Environment variables: process.env, dotenv
- CORS: cors middleware
- Authentication patterns: sessions, JWT
- File uploads: multer
- Database connections: connecting to MongoDB, PostgreSQL

Mix of:
- "How do I X in Express?" → code example
- "What's middleware?" → explanation with example
- "How do I handle X?" → practical solution
- Code snippet → "This Express code does X because..."

JiYou should show modern async/await patterns.""",
    },

    "django_flask": {
        "count": 600,
        "description": "Django and Flask web frameworks",
        "prompt": """Generate dialogue pairs teaching Django and Flask.

The SOURCE is a question about Django or Flask, TARGET is JiYou's explanation.

Include Django topics:
- Project structure: manage.py, settings, apps
- Models: defining models, fields, migrations
- Views: function-based, class-based views
- URLs: url patterns, path(), include()
- Templates: template language, inheritance, filters
- Forms: Form classes, ModelForm, validation
- ORM: queries, filter, get, create, update, delete, Q objects
- Admin: registering models, customization
- Authentication: User model, login, logout, @login_required
- Django REST Framework basics

Include Flask topics:
- App setup: Flask(__name__), app.run()
- Routes: @app.route, methods, URL parameters
- Request: request.args, request.form, request.json
- Response: return, jsonify, make_response
- Templates: Jinja2, render_template
- Blueprints for modular apps
- Flask extensions: Flask-SQLAlchemy, Flask-Login
- Database with SQLAlchemy ORM
- Error handlers: @app.errorhandler

Mix of:
- "How do I X in Django/Flask?" → code example
- "What's the difference between Django and Flask?" → comparison
- "How do I set up X?" → step-by-step
- Code snippet → "This does X because..."

JiYou should show best practices for both frameworks.""",
    },

    "fastapi_async": {
        "count": 500,
        "description": "FastAPI async endpoints, Pydantic, dependency injection",
        "prompt": """Generate dialogue pairs teaching FastAPI.

The SOURCE is a question about FastAPI, TARGET is JiYou's explanation.

Include varied topics:
- Setup: FastAPI(), uvicorn
- Path operations: @app.get, @app.post, @app.put, @app.delete
- Path parameters and query parameters
- Request body with Pydantic models
- Pydantic: BaseModel, Field, validation, nested models
- Response models: response_model parameter
- Async endpoints: async def, await
- Dependency injection: Depends()
- Database with SQLAlchemy (async)
- Authentication: OAuth2, JWT tokens
- Error handling: HTTPException, custom exception handlers
- Background tasks: BackgroundTasks
- File uploads: UploadFile
- OpenAPI documentation: automatic docs, customization
- Middleware
- CORS configuration
- Testing FastAPI apps

Mix of:
- "How do I X in FastAPI?" → code example
- "What's the advantage of FastAPI?" → comparison
- "How do I validate X?" → Pydantic example
- Code snippet → "This FastAPI code does X because..."

JiYou should show async patterns and Pydantic validation.""",
    },

    "rust_basics": {
        "count": 500,
        "description": "Rust ownership, borrowing, lifetimes, traits",
        "prompt": """Generate dialogue pairs teaching Rust.

The SOURCE is a question about Rust, TARGET is JiYou's explanation.

Include varied topics:
- Basic syntax: fn main, let, println!, cargo
- Variables: let, mut, shadowing, constants
- Data types: i32, u64, f64, bool, char, &str, String
- Ownership: move semantics, copy trait
- Borrowing: & references, &mut mutable references
- Lifetimes: 'a syntax, lifetime annotations
- Structs and impl blocks
- Enums: Option<T>, Result<T, E>, pattern matching
- Match expressions, if let
- Vectors: Vec<T>, push, pop, iteration
- Strings: String vs &str, to_string()
- Error handling: Result, ? operator, unwrap, expect
- Traits: defining, implementing, trait bounds
- Generics: generic functions, generic structs
- Modules: mod, pub, use, crate structure
- Collections: HashMap, HashSet
- Iterators and closures
- Testing: #[test], assert!, cargo test

Mix of:
- "How do I X in Rust?" → code example
- "Why does the borrow checker complain about X?" → ownership explanation
- "What's the difference between X and Y?" → comparison
- Code snippet → "This Rust code does X because..."

JiYou should explain ownership/borrowing concepts clearly.""",
    },

    # =========================================================================
    # TIER 4: DATA & DATABASES (~2,500 items)
    # =========================================================================

    "sql_databases": {
        "count": 700,
        "description": "SQL queries, JOINs, indexes, transactions",
        "prompt": """Generate dialogue pairs teaching SQL.

The SOURCE is a question about SQL, TARGET is JiYou's explanation.

Include varied topics:
- SELECT basics: columns, *, FROM, WHERE
- Filtering: =, <>, <, >, IN, BETWEEN, LIKE, IS NULL
- Sorting: ORDER BY, ASC, DESC
- Limiting: LIMIT, OFFSET, TOP
- Aggregates: COUNT, SUM, AVG, MIN, MAX
- GROUP BY and HAVING
- JOINs: INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL JOIN
- JOIN conditions, multiple joins
- Subqueries: in WHERE, in FROM, correlated subqueries
- INSERT: single row, multiple rows
- UPDATE: SET, WHERE clause importance
- DELETE: WHERE clause, TRUNCATE vs DELETE
- Table creation: CREATE TABLE, data types, constraints
- Constraints: PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL, CHECK
- Indexes: CREATE INDEX, when to use, performance
- ALTER TABLE: add column, modify, drop
- Views: CREATE VIEW, when to use
- Transactions: BEGIN, COMMIT, ROLLBACK, ACID
- Common patterns: pagination, search, reporting queries
- Performance: EXPLAIN, index usage, query optimization
- Database-specific: PostgreSQL vs MySQL differences

Mix of:
- "How do I X in SQL?" → query example
- "What's the difference between X and Y?" → comparison
- "Write a query to X" → solution
- "Why is this query slow?" → optimization tips

JiYou should show clear, well-formatted SQL queries.""",
    },

    "nosql_databases": {
        "count": 500,
        "description": "MongoDB, Redis, document and key-value stores",
        "prompt": """Generate dialogue pairs teaching NoSQL databases.

The SOURCE is a question about NoSQL, TARGET is JiYou's explanation.

Include MongoDB topics:
- Document structure: JSON/BSON, collections, databases
- CRUD: insertOne, find, updateOne, deleteOne
- Query operators: $eq, $gt, $in, $and, $or
- Update operators: $set, $inc, $push, $pull
- Aggregation pipeline: $match, $group, $sort, $project
- Indexing: createIndex, compound indexes
- Schema design: embedding vs referencing

Include Redis topics:
- Data types: strings, lists, sets, hashes, sorted sets
- Commands: GET, SET, LPUSH, RPUSH, SADD, HSET
- Key expiration: EXPIRE, TTL
- Use cases: caching, sessions, rate limiting, pub/sub

Include concepts:
- SQL vs NoSQL: when to use each
- CAP theorem basics
- Document vs key-value vs column-family vs graph

Mix of:
- "How do I X in MongoDB?" → query example
- "When should I use Redis?" → use case explanation
- "What's the difference between X and Y?" → comparison
- "How do I model X?" → schema design

JiYou should explain practical use cases and tradeoffs.""",
    },

    "data_formats": {
        "count": 400,
        "description": "JSON, XML, YAML, CSV parsing and generation",
        "prompt": """Generate dialogue pairs about data formats.

The SOURCE is a question about data formats, TARGET is JiYou's explanation.

Include topics:
- JSON: syntax, objects, arrays, data types, parsing/stringify
- JSON in Python: json.loads, json.dumps, file handling
- JSON in JavaScript: JSON.parse, JSON.stringify
- XML: elements, attributes, namespaces, basic structure
- XML parsing: DOM vs SAX, ElementTree (Python), DOMParser (JS)
- YAML: syntax, indentation, lists, maps, multiline strings
- YAML in Python: PyYAML, safe_load, dump
- CSV: format, headers, quoting, escaping
- CSV in Python: csv module, DictReader, DictWriter
- Data serialization concepts
- Format comparison: JSON vs XML vs YAML vs CSV
- Common issues: encoding, special characters, validation
- Schema validation: JSON Schema basics

Mix of:
- "How do I parse X format?" → code example
- "What's the difference between JSON and YAML?" → comparison
- "How do I convert X to Y?" → conversion code
- Data snippet → "This represents X"

JiYou should show practical parsing/generation code.""",
    },

    "orm_patterns": {
        "count": 400,
        "description": "SQLAlchemy, Prisma, Entity Framework ORM patterns",
        "prompt": """Generate dialogue pairs about ORM patterns.

The SOURCE is a question about ORMs, TARGET is JiYou's explanation.

Include SQLAlchemy topics:
- Model definition: declarative base, Column types
- Relationships: ForeignKey, relationship(), backref
- Session: add, commit, query, filter, first, all
- Query building: filter, order_by, limit, join

Include general ORM concepts:
- What is an ORM and why use it
- Migrations: creating, running, rolling back
- N+1 query problem and solutions
- Lazy vs eager loading
- Transactions in ORMs
- Raw SQL when needed
- Model relationships: one-to-one, one-to-many, many-to-many
- Query optimization tips

Include Prisma basics (for Node.js):
- Schema definition, prisma generate
- Client usage: create, findMany, update, delete

Include Entity Framework basics (for C#):
- DbContext, DbSet, migrations
- LINQ queries with EF

Mix of:
- "How do I X with SQLAlchemy?" → code example
- "What's the N+1 problem?" → explanation with solution
- "How do I model X relationship?" → schema design
- "When should I use raw SQL?" → guidance

JiYou should show practical ORM usage patterns.""",
    },

    # =========================================================================
    # TIER 5: CS FUNDAMENTALS (~4,000 items)
    # =========================================================================

    "data_structures": {
        "count": 800,
        "description": "Arrays, linked lists, trees, graphs, hash tables",
        "prompt": """Generate dialogue pairs teaching data structures.

The SOURCE is a question about data structures, TARGET is JiYou's explanation.

Include varied topics:
- Arrays: indexing, operations, time complexity, dynamic arrays
- Linked Lists: singly linked, doubly linked, operations, use cases
- Stacks: LIFO, push, pop, peek, implementations, use cases
- Queues: FIFO, enqueue, dequeue, implementations, priority queues
- Hash Tables: hashing, collisions, chaining, open addressing, load factor
- Trees: terminology (root, leaf, height, depth), traversals
- Binary Trees: structure, properties
- Binary Search Trees: insert, search, delete, balancing
- Balanced Trees: AVL, Red-Black tree concepts
- Heaps: min-heap, max-heap, heapify, heap sort, priority queue
- Graphs: vertices, edges, directed, undirected, weighted
- Graph representations: adjacency list, adjacency matrix
- Graph traversals: BFS, DFS
- Tries: prefix trees, autocomplete use case
- Time/space complexity for each structure

Mix of:
- "What is a X?" → explanation with example
- "When should I use X vs Y?" → comparison with use cases
- "How do I implement X?" → code skeleton
- "What's the time complexity of X?" → Big-O analysis
- "Give me an example of using X" → practical application

JiYou should explain with diagrams (described) and code examples.""",
    },

    "algorithms": {
        "count": 800,
        "description": "Sorting, searching, recursion, dynamic programming",
        "prompt": """Generate dialogue pairs teaching algorithms.

The SOURCE is a question about algorithms, TARGET is JiYou's explanation.

Include varied topics:
- Big-O notation: O(1), O(log n), O(n), O(n log n), O(n^2), O(2^n)
- Analyzing time and space complexity
- Sorting: bubble, selection, insertion, merge, quick, heap sort
- Searching: linear search, binary search
- Recursion: base case, recursive case, call stack
- Divide and conquer: merge sort, quick sort pattern
- Two pointers technique
- Sliding window technique
- Dynamic programming: overlapping subproblems, memoization, tabulation
- Classic DP problems: fibonacci, knapsack, longest common subsequence
- Greedy algorithms: when they work, examples
- Graph algorithms: BFS, DFS, Dijkstra's, topological sort
- String algorithms: pattern matching, string manipulation
- Binary search variations
- Backtracking: N-queens, subset sum
- Problem-solving approach: understand, plan, code, test

Mix of:
- "How does X algorithm work?" → step-by-step explanation
- "What's the time complexity of X?" → analysis
- "When should I use X vs Y?" → comparison
- "How do I solve X problem?" → approach and solution
- Pseudocode → "This implements X because..."

JiYou should explain the intuition behind algorithms.""",
    },

    "design_patterns": {
        "count": 600,
        "description": "Creational, structural, behavioral patterns, SOLID",
        "prompt": """Generate dialogue pairs teaching design patterns.

The SOURCE is a question about patterns, TARGET is JiYou's explanation.

Include SOLID principles:
- Single Responsibility Principle
- Open/Closed Principle
- Liskov Substitution Principle
- Interface Segregation Principle
- Dependency Inversion Principle

Include Creational patterns:
- Singleton: when to use, implementation, issues
- Factory Method: creating objects without specifying class
- Abstract Factory: families of related objects
- Builder: complex object construction
- Prototype: cloning objects

Include Structural patterns:
- Adapter: making incompatible interfaces work together
- Decorator: adding behavior dynamically
- Facade: simplified interface to complex subsystem
- Proxy: placeholder for another object
- Composite: tree structures

Include Behavioral patterns:
- Observer: publish-subscribe, event handling
- Strategy: interchangeable algorithms
- Command: encapsulating requests as objects
- State: changing behavior based on state
- Template Method: skeleton of algorithm

Mix of:
- "What is the X pattern?" → explanation with example
- "When should I use X?" → use cases
- "What's the difference between X and Y?" → comparison
- Code smell → "Apply X pattern to fix this"
- "Give me an example of X" → code example

JiYou should show practical examples with code.""",
    },

    # =========================================================================
    # TIER 6: TOOLS & PRACTICES (~4,500 items)
    # =========================================================================

    "git_version_control": {
        "count": 600,
        "description": "Git commands, branching, merging, workflows",
        "prompt": """Generate dialogue pairs teaching Git.

The SOURCE is a question about Git, TARGET is JiYou's explanation.

Include varied topics:
- Basics: init, clone, status, add, commit, push, pull
- Viewing history: log, diff, show, blame
- Branching: branch, checkout, switch, branch -d
- Merging: merge, resolving conflicts
- Rebasing: rebase, interactive rebase
- Remote: remote add, fetch, pull vs fetch
- Stashing: stash, stash pop, stash list
- Undoing changes: reset, revert, checkout, restore
- Tags: tag, annotated tags
- .gitignore: patterns, common entries
- Workflows: feature branches, Git Flow, GitHub Flow
- Pull requests / Merge requests: process, reviews
- Cherry-pick: selecting specific commits
- Reflog: recovering lost commits
- Common issues: detached HEAD, merge conflicts
- Best practices: commit messages, branch naming

Mix of:
- "How do I X in Git?" → command example
- "What's the difference between X and Y?" → comparison
- "How do I undo X?" → recovery steps
- "What does this error mean?" → explanation and fix
- Scenario → "Use these commands to solve it"

JiYou should show practical Git workflows.""",
    },

    "testing_practices": {
        "count": 500,
        "description": "Unit testing, integration testing, TDD, mocking",
        "prompt": """Generate dialogue pairs teaching software testing.

The SOURCE is a question about testing, TARGET is JiYou's explanation.

Include varied topics:
- Types of testing: unit, integration, e2e, acceptance
- Unit testing principles: isolation, single assertion, fast
- Test structure: Arrange-Act-Assert (AAA)
- Test naming conventions
- pytest basics: test functions, assertions, fixtures
- Jest basics: describe, it/test, expect, matchers
- Mocking: why, when, mock objects, stubs, spies
- pytest mocking: monkeypatch, mock, MagicMock
- Jest mocking: jest.fn(), jest.mock()
- Test fixtures: setup, teardown, shared fixtures
- Code coverage: what it means, tools, limitations
- TDD: Red-Green-Refactor cycle, benefits
- Testing async code
- Testing API endpoints
- Snapshot testing
- Property-based testing concepts
- Common testing mistakes
- What to test vs what not to test

Mix of:
- "How do I test X?" → code example
- "What's the difference between X and Y?" → comparison
- "How do I mock X?" → mocking example
- "What should I test?" → guidance
- Code → "Write tests for this"

JiYou should show practical test code examples.""",
    },

    "devops_cicd": {
        "count": 700,
        "description": "Docker, CI/CD, GitHub Actions, deployment",
        "prompt": """Generate dialogue pairs teaching DevOps basics.

The SOURCE is a question about DevOps, TARGET is JiYou's explanation.

Include Docker topics:
- Containers vs VMs
- Dockerfile: FROM, COPY, RUN, CMD, EXPOSE
- Building images: docker build, tagging
- Running containers: docker run, -p, -v, -e
- Docker Compose: docker-compose.yml, services, volumes
- Common patterns: multi-stage builds

Include CI/CD topics:
- What is CI/CD
- GitHub Actions: workflow files, jobs, steps, triggers
- Common actions: checkout, setup-node, cache
- Running tests in CI
- Deployment automation
- Secrets management
- Pipeline stages: build, test, deploy

Include deployment topics:
- Environment variables
- Configuration management
- Basic cloud concepts (AWS, GCP, Azure overview)
- Deployment strategies: rolling, blue-green
- Monitoring basics

Mix of:
- "How do I X with Docker?" → command/file example
- "How do I set up CI for X?" → workflow example
- "What's the difference between X and Y?" → comparison
- "How do I deploy X?" → step-by-step
- Dockerfile/workflow → "This does X because..."

JiYou should show practical configuration examples.""",
    },

    "security_basics": {
        "count": 600,
        "description": "OWASP top 10, authentication, encryption basics",
        "prompt": """Generate dialogue pairs teaching web security.

The SOURCE is a question about security, TARGET is JiYou's explanation.

Include OWASP Top 10:
- Injection (SQL injection, command injection): prevention
- Broken Authentication: secure session management
- Sensitive Data Exposure: encryption, HTTPS
- XML External Entities (XXE): prevention
- Broken Access Control: authorization checks
- Security Misconfiguration: defaults, hardening
- Cross-Site Scripting (XSS): types, prevention, escaping
- Insecure Deserialization
- Using Components with Known Vulnerabilities
- Insufficient Logging & Monitoring

Include authentication/authorization:
- Password hashing: bcrypt, argon2
- Sessions vs tokens
- JWT: structure, signing, verification, refresh tokens
- OAuth 2.0 basics
- Role-based access control (RBAC)

Include general security:
- HTTPS and TLS
- CORS: what it is, configuration
- CSRF: what it is, prevention tokens
- Input validation and sanitization
- Rate limiting
- Security headers: CSP, X-Frame-Options

Mix of:
- "What is X vulnerability?" → explanation with example
- "How do I prevent X?" → mitigation code/config
- "Is this code secure?" → security review
- "How do I implement X securely?" → secure pattern

JiYou should emphasize practical prevention techniques.""",
    },

    "api_design": {
        "count": 500,
        "description": "REST, GraphQL, HTTP methods, OpenAPI",
        "prompt": """Generate dialogue pairs teaching API design.

The SOURCE is a question about APIs, TARGET is JiYou's explanation.

Include REST topics:
- REST principles: stateless, resource-based, uniform interface
- HTTP methods: GET, POST, PUT, PATCH, DELETE semantics
- Status codes: 200, 201, 204, 400, 401, 403, 404, 500
- Resource naming: nouns, plural, nested resources
- Query parameters: filtering, sorting, pagination
- Request/response formats: JSON
- Versioning: URL, header, query param approaches
- HATEOAS concept
- Idempotency

Include GraphQL topics:
- Query vs Mutation vs Subscription
- Schema definition: types, queries, mutations
- Resolvers
- GraphQL vs REST: tradeoffs

Include general topics:
- API authentication: API keys, OAuth, JWT
- Rate limiting
- Error handling: consistent error format
- Documentation: OpenAPI/Swagger
- API versioning strategies
- Pagination patterns: offset, cursor
- Caching: ETag, Cache-Control

Mix of:
- "How should I design X endpoint?" → RESTful design
- "What status code for X?" → correct status
- "What's the difference between X and Y?" → comparison
- "How do I handle X in my API?" → pattern
- API design → "This could be improved by..."

JiYou should show RESTful best practices.""",
    },

    "debugging_tools": {
        "count": 500,
        "description": "Browser devtools, debuggers, profiling, logging",
        "prompt": """Generate dialogue pairs teaching debugging.

The SOURCE is a question about debugging, TARGET is JiYou's explanation.

Include browser devtools:
- Elements panel: inspecting, modifying DOM
- Console: logging, evaluating expressions, errors
- Network panel: requests, responses, timing
- Sources panel: breakpoints, stepping, watch
- Performance panel: profiling, bottlenecks
- Application panel: storage, cookies

Include debugging techniques:
- console.log debugging: strategic placement
- Breakpoints: conditional, logpoints
- Step over, step into, step out
- Watch expressions
- Call stack analysis
- Rubber duck debugging
- Binary search debugging

Include Python debugging:
- print debugging
- pdb: breakpoints, commands
- IDE debuggers: VS Code, PyCharm
- logging module: levels, formatters

Include general:
- Reading error messages and stack traces
- Reproducing bugs
- Systematic debugging approach
- Performance profiling basics
- Memory leak detection
- Common bug patterns

Mix of:
- "How do I debug X?" → technique
- "What does this error mean?" → explanation
- "How do I use X tool?" → walkthrough
- "Why is my code slow?" → profiling approach
- Bug scenario → "Debug by doing X"

JiYou should teach systematic debugging.""",
    },

    "shell_scripting": {
        "count": 500,
        "description": "Bash scripting, command line, common utilities",
        "prompt": """Generate dialogue pairs teaching shell/Bash.

The SOURCE is a question about shell, TARGET is JiYou's explanation.

Include command line basics:
- Navigation: cd, ls, pwd, mkdir, rm, cp, mv
- File viewing: cat, less, head, tail, grep
- File manipulation: touch, chmod, chown
- Text processing: grep, sed, awk basics
- Pipes and redirection: |, >, >>, <, 2>
- Finding: find, locate, which

Include Bash scripting:
- Shebang: #!/bin/bash
- Variables: assignment, $VAR, ${VAR}
- Special variables: $0, $1, $#, $@, $?
- Conditionals: if, elif, else, test, [[ ]]
- Loops: for, while, until
- Functions: definition, calling, return values
- Command substitution: $(command)
- Arithmetic: ((expression)), $((expression))
- String manipulation in Bash
- Exit codes and error handling
- Reading input: read
- Script arguments

Include common utilities:
- curl: making HTTP requests
- jq: parsing JSON
- xargs: building commands
- sort, uniq, wc
- Environment variables: export, env

Mix of:
- "How do I X in Bash?" → command/script
- "What does X command do?" → explanation
- "How do I process X?" → pipeline
- Script → "This script does X"
- Task → "Use these commands"

JiYou should show practical one-liners and scripts.""",
    },
}


# =============================================================================
# GENERATION FUNCTIONS
# =============================================================================

def parse_json_response(response_text: str) -> List[Dict[str, str]]:
    """Extract JSON array from model response."""
    text = response_text.strip()

    # Look for array brackets
    start = text.find('[')
    end = text.rfind(']')

    if start != -1 and end != -1 and end > start:
        json_str = text[start:end + 1]
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    # Try to parse line by line for individual objects
    pairs = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                obj = json.loads(line)
                if 'source' in obj and 'target' in obj:
                    pairs.append(obj)
            except json.JSONDecodeError:
                continue
        # Handle trailing commas
        elif line.startswith('{') and line.endswith('},'):
            try:
                obj = json.loads(line[:-1])
                if 'source' in obj and 'target' in obj:
                    pairs.append(obj)
            except json.JSONDecodeError:
                continue

    return pairs


def generate_batch(
    category: str,
    category_info: Dict[str, Any],
    batch_num: int,
    batch_size: int = 20,
    existing_sources: set = None,
) -> List[Dict[str, str]]:
    """Generate a batch of dialogue pairs using Grok API."""

    avoid_examples = ""
    if existing_sources and len(existing_sources) > 0:
        samples = list(existing_sources)[:10]
        avoid_examples = f"\n\nAvoid these already-used sources:\n{json.dumps(samples, indent=2)}"

    prompt = f"""Generate {batch_size} unique dialogue pairs for: {category.replace('_', ' ')}

{category_info['prompt']}

Format: Return ONLY a valid JSON array of objects with "source" and "target" fields.
{avoid_examples}

Generate batch {batch_num} with {batch_size} NEW unique pairs (different from any shown above):"""

    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates programming education dialogue training data. Always respond with valid JSON arrays only, no other text. Each item should have 'source' (question/code) and 'target' (explanation/answer) fields."},
            {"role": "user", "content": prompt}
        ]

        response_text = call_grok_api(messages, temperature=0.9, max_tokens=4000)
        pairs = parse_json_response(response_text)
        return pairs

    except Exception as e:
        print(f"  Error generating batch: {e}")
        return []


def generate_category(
    category: str,
    target_count: int,
    batch_size: int = 20,
    dry_run: bool = False,
    existing_pairs: List[Dict] = None,
) -> List[Dict[str, str]]:
    """Generate all dialogue pairs for a category."""

    if category not in CATEGORIES:
        print(f"Unknown category: {category}")
        return []

    category_info = CATEGORIES[category]
    print(f"\nGenerating {category}: {category_info['description']}")
    print(f"  Target: {target_count} pairs")

    if dry_run:
        print("  [DRY RUN - would generate here]")
        return []

    # Resume from existing if provided
    all_pairs = existing_pairs or []
    seen_sources = set(p.get('source', '').strip().lower() for p in all_pairs)

    if all_pairs:
        print(f"  Resuming from {len(all_pairs)} existing pairs")

    batch_num = len(all_pairs) // batch_size

    while len(all_pairs) < target_count:
        batch_num += 1
        remaining = target_count - len(all_pairs)
        current_batch_size = min(batch_size, remaining + 5)

        print(f"  Batch {batch_num}: generating {current_batch_size} pairs...", end=" ", flush=True)

        pairs = generate_batch(
            category, category_info, batch_num,
            current_batch_size, seen_sources
        )

        # Deduplicate by source
        new_pairs = []
        for pair in pairs:
            source = pair.get('source', '').strip().lower()
            if source and source not in seen_sources:
                seen_sources.add(source)
                new_pairs.append(pair)

        all_pairs.extend(new_pairs)
        print(f"got {len(new_pairs)} unique ({len(all_pairs)}/{target_count})")

        # Rate limiting
        time.sleep(1.0)

        # Safety limit
        if batch_num > target_count // batch_size + 50:
            print(f"  Reached batch limit, stopping at {len(all_pairs)} pairs")
            break

    return all_pairs[:target_count]


def create_lesson_file(
    category: str,
    pairs: List[Dict[str, str]],
    lesson_id: str,
    lesson_num: int,
    output_dir: Path,
) -> Path:
    """Create a JCUR lesson file from dialogue pairs."""

    category_info = CATEGORIES.get(category, {})
    clean_category = category.replace('_', ' ').title()

    lesson = {
        "lesson_id": lesson_id,
        "title": f"Coding: {clean_category}",
        "description": category_info.get("description", f"Programming skills for {category}"),
        "category": "coding",
        "difficulty": 3,
        "estimated_minutes": max(30, len(pairs) // 5),
        "tags": ["coding", "programming", category.split('_')[0]],
        "items": []
    }

    for i, pair in enumerate(pairs):
        item = {
            "id": f"code_{category}_{i+1:04d}",
            "type": "dialogue",
            "source": pair.get("source", ""),
            "target": pair.get("target", ""),
            "context": category,
        }
        lesson["items"].append(item)

    filename = f"{lesson_num:03d}_{category}.json"
    filepath = output_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(lesson, f, indent=2, ensure_ascii=False)

    print(f"  Created: {filename} ({len(pairs)} items)")
    return filepath


def load_existing_lesson(output_dir: Path, category: str) -> tuple:
    """Load existing lesson file for resumption."""
    for f in output_dir.glob(f"*_{category}.json"):
        try:
            with open(f) as fp:
                lesson = json.load(fp)
            pairs = [{"source": i["source"], "target": i["target"]} for i in lesson.get("items", [])]
            lesson_num = int(f.stem.split('_')[0])
            return pairs, lesson_num
        except:
            pass
    return [], None


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive coding curriculum using Grok API"
    )
    parser.add_argument(
        "--category", "-c",
        help="Generate specific category only"
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        help="Override count for category"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=20,
        help="Pairs per batch (default: 20)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(__file__).parent.parent / "curricula/coding.jcur/lessons",
        help="Output directory for lesson files"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Generate all categories"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without calling API"
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available categories"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing lesson files"
    )

    args = parser.parse_args()

    if args.list_categories:
        print("Available coding categories:\n")
        total = 0
        for name, info in CATEGORIES.items():
            print(f"  {name:25s} - {info['count']:5d} pairs - {info['description'][:50]}...")
            total += info['count']
        print(f"\n  {'TOTAL':25s} - {total:5d} pairs across {len(CATEGORIES)} categories")
        return

    # Ensure output directory exists
    args.output.mkdir(parents=True, exist_ok=True)

    # Determine which categories to generate
    if args.category:
        categories = [args.category]
    elif args.all:
        categories = list(CATEGORIES.keys())
    else:
        print("Specify --category NAME or --all to generate")
        print("Use --list-categories to see available categories")
        return

    print("=" * 60)
    print("CODING CURRICULUM GENERATOR")
    print("=" * 60)
    print(f"Using Grok API (grok-4-1-fast-non-reasoning)")
    print(f"Output directory: {args.output}")
    print(f"Categories to generate: {len(categories)}")

    if args.dry_run:
        print("[DRY RUN MODE]")
    else:
        get_api_key()
        print("Grok API key found")

    # Generate each category
    all_results = {}
    lesson_num = 1

    for category in categories:
        # Check for existing lesson to determine lesson number
        existing_pairs = []
        if args.resume:
            existing_pairs, existing_num = load_existing_lesson(args.output, category)
            if existing_num:
                lesson_num = existing_num
        else:
            # Find next available lesson number
            existing_files = list(args.output.glob(f"*_{category}.json"))
            if existing_files:
                # Skip if already exists and not resuming
                print(f"\nSkipping {category}: lesson file already exists (use --resume to continue)")
                lesson_num += 1
                continue

        count = args.count if args.count else CATEGORIES[category]["count"]
        pairs = generate_category(
            category=category,
            target_count=count,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            existing_pairs=existing_pairs,
        )

        if pairs:
            lesson_id = f"coding_{category}"
            create_lesson_file(
                category=category,
                pairs=pairs,
                lesson_id=lesson_id,
                lesson_num=lesson_num,
                output_dir=args.output,
            )
            all_results[category] = len(pairs)

        lesson_num += 1

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)
    total = 0
    for cat, count in all_results.items():
        print(f"  {cat:30s}: {count:5d} pairs")
        total += count
    print("-" * 60)
    print(f"  {'TOTAL':30s}: {total:5d} pairs")
    print(f"\nLesson files created in: {args.output}")


if __name__ == "__main__":
    main()
