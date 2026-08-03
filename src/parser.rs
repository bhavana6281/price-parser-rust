use crate::currency;
use crate::Price;
use once_cell::sync::Lazy;
use regex::Regex;
use rust_decimal::prelude::ToPrimitive;
use rust_decimal::Decimal;
use std::str::FromStr;

static GENERIC_PRICE_RE: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?x)([.]?\d[\d\s.,']*)\s*(?:[^%\d]|$)").expect("generic price regex must compile")
});

static EURO_SPACE_RE: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?x)([\d\s.,']*?\d)\s*€\s+(\d{2})(?:$|[^\d])")
        .expect("spaced euro regex must compile")
});

static EURO_TIGHT_RE: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?x)([\d\s.,']*?\d)\s*€(\d+)(?:$|[^\d])").expect("tight euro regex must compile")
});

#[derive(Debug, Clone, Copy, Default)]
pub struct ParseOptions<'a> {
    pub currency_hint: Option<&'a str>,
    pub decimal_separator: Option<char>,
    pub digit_group_separator: Option<char>,
}

pub fn parse_price(price: Option<&str>, options: ParseOptions<'_>) -> Price {
    let currency = currency::extract_currency_symbol(price, options.currency_hint)
        .map(|value| value.trim().to_string());

    let owned_price = match (price, options.digit_group_separator) {
        (Some(value), Some(separator)) => Some(value.replace(separator, "")),
        (Some(value), None) => Some(value.to_string()),
        (None, _) => None,
    };

    let amount_text = owned_price.as_deref().and_then(extract_price_text);
    let amount = amount_text
        .as_deref()
        .and_then(|text| parse_number(text, options.decimal_separator));

    Price::new(amount, currency, amount_text)
}

pub fn extract_currency_symbol(price: Option<&str>, currency_hint: Option<&str>) -> Option<String> {
    currency::extract_currency_symbol(price, currency_hint)
}

fn collapse_whitespace(input: &str) -> String {
    let mut output = String::with_capacity(input.len());
    let mut in_whitespace = false;
    for ch in input.chars() {
        if ch.is_whitespace() {
            if !in_whitespace {
                output.push(' ');
                in_whitespace = true;
            }
        } else {
            output.push(ch);
            in_whitespace = false;
        }
    }
    output
}

fn euro_decimal_match(price: &str) -> Option<String> {
    let matched = EURO_SPACE_RE
        .find(price)
        .or_else(|| EURO_TIGHT_RE.find(price))?;
    Some(matched.as_str().replace(' ', ""))
}

pub fn extract_price_text(price: &str) -> Option<String> {
    let normalized = collapse_whitespace(price);

    if normalized.matches('€').count() == 1 {
        if let Some(value) = euro_decimal_match(&normalized) {
            return Some(value);
        }
    }

    if let Some(captures) = GENERIC_PRICE_RE.captures(&normalized) {
        let mut value = captures
            .get(1)?
            .as_str()
            .trim_end_matches([',', '.'])
            .to_string();
        value.retain(|ch| ch != '\'');
        if value.matches('.').count() == 1 {
            return Some(value.trim().to_string());
        }
        return Some(value.trim_start_matches([',', '.']).trim().to_string());
    }

    if normalized.to_lowercase().contains("free") {
        return Some("0".to_string());
    }
    None
}

pub fn get_decimal_separator(price: &str) -> Option<char> {
    let (separator_index, separator) = price
        .char_indices()
        .rev()
        .find(|(_, ch)| matches!(ch, '.' | ',' | '€'))?;
    let suffix = &price[separator_index + separator.len_utf8()..];
    if suffix.is_empty() || !suffix.chars().all(|ch| ch.is_ascii_digit()) {
        return None;
    }
    let digits = suffix.chars().count();
    if digits == 1 || digits == 2 || digits >= 4 {
        Some(separator)
    } else {
        None
    }
}

pub fn parse_number(num: &str, decimal_separator: Option<char>) -> Option<Decimal> {
    if num.is_empty() {
        return None;
    }
    let mut normalized: String = num.chars().filter(|ch| !ch.is_whitespace()).collect();
    let decimal_separator = decimal_separator.or_else(|| get_decimal_separator(&normalized));

    match decimal_separator {
        None => {
            normalized = normalized.replace(['.', ','], "");
        }
        Some('.') => {
            normalized = normalized.replace(',', "");
        }
        Some(',') => {
            normalized = normalized.replace('.', "").replace(',', ".");
        }
        Some('€') => {
            normalized = normalized.replace(['.', ','], "").replace('€', ".");
        }
        Some(_) => return None,
    }

    Decimal::from_str(&normalized).ok()
}

/// Compatibility helper retained from the initial port.
pub fn parse_amount(raw_amount: &str) -> Option<f64> {
    parse_number(raw_amount, None).and_then(|value| value.to_f64())
}

#[cfg(test)]
mod tests {
    use super::{
        extract_price_text, get_decimal_separator, parse_number, parse_price, ParseOptions,
    };
    use rust_decimal::Decimal;
    use std::str::FromStr;

    #[test]
    fn upstream_documented_extraction_cases() {
        let cases = [
            ("price: $12.99", Some("12.99")),
            ("Free", Some("0")),
            ("FREE SHIPPING", Some("0")),
            ("Foo", None),
            ("1,235 USD", Some("1,235")),
            ("35€ 99", Some("35€99")),
            ("35€ 999", Some("35")),
            ("1,235€ 99", Some("1,235€99")),
            ("50% OFF", None),
            ("$.75", Some(".75")),
            ("CHF 1'049,95", Some("1049,95")),
        ];
        for (input, expected) in cases {
            assert_eq!(extract_price_text(input).as_deref(), expected, "{input}");
        }
        assert_eq!(extract_price_text("35€99!").as_deref(), Some("35€99!"));
    }

    #[test]
    fn upstream_documented_separator_cases() {
        assert_eq!(get_decimal_separator("1000"), None);
        assert_eq!(get_decimal_separator("12.99"), Some('.'));
        assert_eq!(get_decimal_separator("12,99"), Some(','));
        assert_eq!(get_decimal_separator("12.999"), None);
        assert_eq!(get_decimal_separator("3,0000"), Some(','));
        assert_eq!(get_decimal_separator("1,235€99"), Some('€'));
        assert_eq!(get_decimal_separator(".75"), Some('.'));
    }

    #[test]
    fn upstream_documented_number_cases() {
        let cases = [
            ("1,234", None, "1234"),
            ("12,34", None, "12.34"),
            ("12,345", None, "12345"),
            ("12€34", None, "12.34"),
            ("1 234.99", None, "1234.99"),
            ("1,235€99", None, "1235.99"),
            ("140.000", Some(','), "140000"),
            ("140.000", Some('.'), "140.000"),
        ];
        for (input, separator, expected) in cases {
            assert_eq!(
                parse_number(input, separator),
                Some(Decimal::from_str(expected).unwrap()),
                "{input}"
            );
        }
    }

    #[test]
    fn options_and_currency_precedence() {
        let parsed = parse_price(
            Some(" 123,456.789 OMR"),
            ParseOptions {
                currency_hint: None,
                decimal_separator: Some('.'),
                digit_group_separator: Some(','),
            },
        );
        assert_eq!(parsed.currency.as_deref(), Some("OMR"));
        assert_eq!(parsed.amount_text.as_deref(), Some("123456.789"));
        assert_eq!(parsed.amount.unwrap().to_string(), "123456.789");

        let hinted = parse_price(
            Some("39.95"),
            ParseOptions {
                currency_hint: Some("GBP"),
                ..ParseOptions::default()
            },
        );
        assert_eq!(hinted.currency.as_deref(), Some("GBP"));
    }
}
