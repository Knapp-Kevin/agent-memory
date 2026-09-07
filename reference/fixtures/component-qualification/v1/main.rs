fn leaf() -> i32 {
    1
}

fn middle() -> i32 {
    leaf()
}

fn top() -> i32 {
    middle()
}

fn main() {
    println!("{}", top());
}
