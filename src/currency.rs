//! Currency recognition ordered to match the Python implementation's precedence.
//!
//! The upstream parser treats a set of symbols as safe, gives dollar-denominated
//! ISO codes priority over `$`, and only then searches the wider symbol/code set.

use crate::currency_data::{CURRENCY_CODES, OTHER_CURRENCY_SYMBOLS, SAFE_CURRENCY_SYMBOLS};

fn find_earliest<'a>(text: &str, candidates: impl IntoIterator<Item = &'a str>) -> Option<String> {
    let mut best: Option<(usize, &str)> = None;
    for candidate in candidates {
        if candidate.is_empty() {
            continue;
        }
        if let Some(index) = text.find(candidate) {
            let is_earlier = match best {
                Some((best_index, _)) => index < best_index,
                None => true,
            };
            if is_earlier {
                best = Some((index, candidate));
            }
        }
    }
    best.map(|(_, value)| value.to_string())
}

fn is_word_character(ch: char) -> bool {
    ch.is_alphanumeric() || ch == '_'
}

fn find_dollar_code(text: &str) -> Option<String> {
    let mut best: Option<(usize, &str)> = None;
    for code in CURRENCY_CODES
        .iter()
        .copied()
        .filter(|code| code.ends_with('D'))
    {
        for (index, _) in text.match_indices(code) {
            let before_ok = match text[..index].chars().next_back() {
                Some(ch) => !is_word_character(ch),
                None => true,
            };
            if !before_ok {
                continue;
            }

            let mut rest = &text[index + code.len()..];
            if let Some(stripped) = rest.strip_prefix('$') {
                rest = stripped;
            }
            let after_ok = match rest.chars().next() {
                Some(ch) => !ch.is_alphabetic() && ch != '_',
                None => true,
            };
            let is_earlier = match best {
                Some((best_index, _)) => index < best_index,
                None => true,
            };
            if after_ok && is_earlier {
                best = Some((index, code));
            }
        }
    }
    best.map(|(_, code)| code.to_string())
}

fn find_safe(text: &str) -> Option<String> {
    find_earliest(text, SAFE_CURRENCY_SYMBOLS.iter().copied())
}

fn find_other(text: &str) -> Option<String> {
    find_earliest(text, OTHER_CURRENCY_SYMBOLS.iter().copied())
}

pub fn extract_currency_symbol(price: Option<&str>, currency_hint: Option<&str>) -> Option<String> {
    if let Some(value) = price.filter(|value| value.contains('$')) {
        if let Some(code) = find_dollar_code(value) {
            return Some(code);
        }
    }
    if let Some(value) = currency_hint.filter(|value| value.contains('$')) {
        if let Some(code) = find_dollar_code(value) {
            return Some(code);
        }
    }
    price
        .and_then(find_safe)
        .or_else(|| currency_hint.and_then(find_safe))
        .or_else(|| price.and_then(find_other))
        .or_else(|| currency_hint.and_then(find_other))
}

#[cfg(test)]
mod tests {
    use super::extract_currency_symbol;

    #[test]
    fn dollar_codes_beat_dollar_symbol() {
        assert_eq!(
            extract_currency_symbol(Some("SGD$4.90"), None).as_deref(),
            Some("SGD")
        );
        assert_eq!(
            extract_currency_symbol(Some("US$:12.99"), None).as_deref(),
            Some("US$")
        );
    }

    #[test]
    fn price_beats_hint() {
        assert_eq!(
            extract_currency_symbol(Some("€ 10"), Some("USD")).as_deref(),
            Some("€")
        );
    }
}
