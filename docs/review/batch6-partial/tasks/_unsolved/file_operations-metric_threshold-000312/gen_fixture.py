import hashlib
import os
import random
import re
import shutil

random.seed(42)

MESSY = '/workspace/messy'
REF = '/workspace/reference'

os.makedirs(MESSY, exist_ok=True)
os.makedirs(REF, exist_ok=True)

# Define the canonical (clean) files with their content
canonical = {
    'main.rs': 'fn main() {\n    println!("Hello, world!");\n}\n',
    'lib.rs': 'pub mod utils;\npub mod parser;\n',
    'utils.rs': 'pub fn add(a: i32, b: i32) -> i32 { a + b }\n',
    'parser.rs': 'pub fn parse(s: &str) -> Vec<&str> { s.split_whitespace().collect() }\n',
    'config.rs': 'pub struct Config { pub debug: bool, pub verbose: bool }\n',
    'error.rs': 'use std::fmt;\npub enum AppError { NotFound, ParseError }\n',
    'handler.rs': 'pub fn handle(input: &str) -> Result<(), String> { Ok(()) }\n',
    'router.rs': 'pub fn route(path: &str) -> &str { path }\n',
    'models.rs': 'pub struct User { pub id: u64, pub name: String }\n',
    'schema.rs': 'pub fn create_schema() -> String { String::from("schema") }\n',
    'auth.rs': 'pub fn authenticate(token: &str) -> bool { !token.is_empty() }\n',
    'cache.rs': 'use std::collections::HashMap;\npub struct Cache { store: HashMap<String,String> }\n',
    'logger.rs': 'pub fn log(msg: &str) { eprintln!("{}", msg); }\n',
    'server.rs': 'pub fn start_server(port: u16) { println!("Listening on {}", port); }\n',
    'client.rs': 'pub fn connect(addr: &str) -> Result<(), String> { Ok(()) }\n',
    'tests.rs': '#[cfg(test)]\nmod tests { #[test] fn it_works() { assert!(true); } }\n',
    'constants.rs': 'pub const MAX_SIZE: usize = 1024;\npub const VERSION: &str = "1.0.0";\n',
    'helpers.rs': 'pub fn clamp(v: i32, lo: i32, hi: i32) -> i32 { v.max(lo).min(hi) }\n',
    'types.rs': 'pub type Result<T> = std::result::Result<T, String>;\n',
    'db.rs': 'pub fn query(sql: &str) -> Vec<String> { vec![] }\n',
    'middleware.rs': 'pub fn apply_middleware(req: &str) -> String { req.to_uppercase() }\n',
    'session.rs': 'pub struct Session { pub id: String, pub user_id: u64 }\n',
    'crypto.rs': 'pub fn hash(data: &[u8]) -> Vec<u8> { data.to_vec() }\n',
    'metrics.rs': 'pub fn record(name: &str, value: f64) { println!("{}: {}", name, value); }\n',
    'events.rs': 'pub enum Event { Start, Stop, Error(String) }\n',
    'pipeline.rs': 'pub fn run_pipeline(steps: Vec<&str>) { for s in steps { println!("{}", s); } }\n',
    'storage.rs': 'pub fn save(key: &str, val: &str) -> bool { true }\n',
    'format.rs': 'pub fn format_date(ts: u64) -> String { format!("{}", ts) }\n',
    'network.rs': 'pub fn fetch(url: &str) -> String { String::new() }\n',
    'thread_pool.rs': 'pub fn spawn_workers(n: usize) { for _ in 0..n {} }\n',
}

# Write reference files
for name, content in canonical.items():
    with open(os.path.join(REF, name), 'w') as f:
        f.write(content)

# Now generate messy versions
# We'll create:
# 1. Some files with correct names and content (easy matches)
# 2. Some files with mangled names (need rename) but correct content
# 3. Some duplicates (same content, different names)
# 4. Some files with wrong content (will be MISMATCH_CONTENT after rename)
# 5. Some extra noise files

messy_entries = []

# Group 1: directly correct (10 files)
direct_correct = list(canonical.keys())[:10]
for name in direct_correct:
    messy_entries.append((name, canonical[name]))

# Group 2: mangled names that clean to correct stems (14 files)
mangled_pairs = [
    ('Config_copy.rs', 'config.rs'),
    ('ERROR_bak.rs', 'error.rs'),
    ('Handler_1.rs', 'handler.rs'),
    ('ROUTER_dup.rs', 'router.rs'),
    ('Models_2.rs', 'models.rs'),
    ('Schema__bak.rs', 'schema.rs'),
    ('Auth_copy_bak.rs', 'auth.rs'),
    ('Cache_3.rs', 'cache.rs'),
    ('Logger_dup.rs', 'logger.rs'),
    ('SERVER_copy.rs', 'server.rs'),
    ('Client_bak.rs', 'client.rs'),
    ('Tests_1.rs', 'tests.rs'),
    ('Constants_2.rs', 'constants.rs'),
    ('Helpers_dup.rs', 'helpers.rs'),
]
for mangled, clean in mangled_pairs:
    messy_entries.append((mangled, canonical[clean]))

# Group 3: duplicates of already-added files (will be removed in dedup)
# Add duplicates of the direct_correct group
dup_entries = [
    ('main_copy.rs', canonical['main.rs']),
    ('lib_dup.rs', canonical['lib.rs']),
    ('utils_bak.rs', canonical['utils.rs']),
    ('parser_2.rs', canonical['parser.rs']),
    ('MAIN_copy.rs', canonical['main.rs']),  # also duplicate of main
]
messy_entries.extend(dup_entries)

# Group 4: files with wrong content (will be MISMATCH_CONTENT after rename)
# These have the correct clean name but wrong content
mismatch_content = [
    ('types.rs', '// wrong content for types\npub type Foo = u8;\n'),
    ('db_copy.rs', '// wrong db content\n'),  # renames to db.rs but wrong content
]
messy_entries.extend(mismatch_content)

# Group 5: files whose clean name doesn't exist in reference (noise)
noise = [
    ('scratch_bak.rs', 'fn scratch() {}\n'),
    ('OLD__test_1.rs', '// old test\n'),
    ('tmp_dup.rs', '// temporary\n'),
]
messy_entries.extend(noise)

# Shuffle
random.shuffle(messy_entries)

# Write messy files
for name, content in messy_entries:
    with open(os.path.join(MESSY, name), 'w') as f:
        f.write(content)

print('Fixture generated.')
print(f'Reference files: {len(os.listdir(REF))}')
print(f'Messy files: {len(os.listdir(MESSY))}')
