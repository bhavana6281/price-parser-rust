#![forbid(unsafe_code)]

pub mod currency;
mod currency_data;
pub mod parser;
pub mod price;

pub use parser::{
    extract_currency_symbol, extract_price_text, get_decimal_separator, parse_amount, parse_number,
    parse_price, ParseOptions,
};
pub use price::Price;
