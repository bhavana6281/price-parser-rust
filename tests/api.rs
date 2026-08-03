use price_parser_rust::{parse_price, ParseOptions};

#[test]
fn parses_localized_price() {
    let price = parse_price(Some("Běžná cena 75 990,00 Kč"), ParseOptions::default());
    assert_eq!(price.amount.unwrap().to_string(), "75990.00");
    assert_eq!(price.currency.as_deref(), Some("Kč"));
    assert_eq!(price.amount_text.as_deref(), Some("75 990,00"));
}

#[test]
fn preserves_none_input() {
    let price = parse_price(None, ParseOptions::default());
    assert_eq!(price.amount, None);
    assert_eq!(price.currency, None);
    assert_eq!(price.amount_text, None);
}

#[test]
fn ignores_percentage_after_first_price() {
    let price = parse_price(
        Some("99,99 EUR (-30,00%) 69,99 EUR"),
        ParseOptions::default(),
    );
    assert_eq!(price.amount.unwrap().to_string(), "99.99");
    assert_eq!(price.currency.as_deref(), Some("EUR"));
    assert_eq!(price.amount_text.as_deref(), Some("99,99"));
}
