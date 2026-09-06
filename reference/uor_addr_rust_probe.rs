use std::io::{self, Read};
use uor_addr::json::address as json_address;

fn main() {
    let mut input = Vec::new();
    io::stdin().read_to_end(&mut input).unwrap();
    let outcome = json_address(&input).unwrap();
    println!("{}", outcome.address);
}
