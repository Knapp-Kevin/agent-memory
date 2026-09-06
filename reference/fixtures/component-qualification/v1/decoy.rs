// decoy fixture
// middle intentionally begins on the same line as main.rs::middle
// decoy_leaf intentionally begins on a different line from main.rs::leaf

fn middle() -> i32 {
    decoy_leaf()
}

// padding keeps the downstream target line distinct
// from main.rs::leaf for file-identity regression detection.

fn decoy_leaf() -> i32 {
    9
}

fn main() {
    println!("{}", middle());
}
