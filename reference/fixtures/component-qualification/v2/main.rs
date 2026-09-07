// v2 removes the old leaf relationship.
// middle remains on the same line as v1 and decoy for identity pressure.
// replacement_leaf moves to a distinct source line for stale-edge detection.

fn middle() -> i32 {
    replacement_leaf()
}

fn top() -> i32 {
    middle()
}

fn replacement_leaf() -> i32 {
    2
}

fn main() {
    println!("{}", top());
}
