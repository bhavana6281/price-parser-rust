use price_parser_rust::{parse_price, ParseOptions, Price};
use serde::{Deserialize, Serialize};
use std::env;
use std::io::{self, BufRead, Write};

#[derive(Debug, Deserialize)]
struct ParseRequest {
    #[serde(alias = "price")]
    input: Option<String>,
    #[serde(default)]
    currency_hint: Option<String>,
    #[serde(default)]
    decimal_separator: Option<String>,
    #[serde(default)]
    digit_group_separator: Option<String>,
}

#[derive(Debug, Serialize)]
struct ParseResponse {
    amount: Option<String>,
    currency: Option<String>,
    amount_text: Option<String>,
}

impl From<Price> for ParseResponse {
    fn from(value: Price) -> Self {
        Self {
            amount: value.amount.map(|amount| amount.to_string()),
            currency: value.currency,
            amount_text: value.amount_text,
        }
    }
}

fn one_char(value: Option<&str>) -> Result<Option<char>, String> {
    match value {
        None => Ok(None),
        Some(text) => {
            let mut chars = text.chars();
            let first = chars
                .next()
                .ok_or_else(|| "separator cannot be empty".to_string())?;
            if chars.next().is_some() {
                return Err(format!("separator must be one character: {text:?}"));
            }
            Ok(Some(first))
        }
    }
}

fn execute(request: ParseRequest) -> Result<ParseResponse, String> {
    let decimal_separator = one_char(request.decimal_separator.as_deref())?;
    let digit_group_separator = one_char(request.digit_group_separator.as_deref())?;
    Ok(parse_price(
        request.input.as_deref(),
        ParseOptions {
            currency_hint: request.currency_hint.as_deref(),
            decimal_separator,
            digit_group_separator,
        },
    )
    .into())
}

fn run_jsonl() -> Result<(), String> {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut output = stdout.lock();
    for line in stdin.lock().lines() {
        let line = line.map_err(|error| error.to_string())?;
        if line.trim().is_empty() {
            continue;
        }
        let response = match serde_json::from_str::<ParseRequest>(&line) {
            Ok(request) => match execute(request) {
                Ok(result) => serde_json::json!({"ok": true, "result": result}),
                Err(error) => serde_json::json!({"ok": false, "error": error}),
            },
            Err(error) => serde_json::json!({"ok": false, "error": error.to_string()}),
        };
        serde_json::to_writer(&mut output, &response).map_err(|error| error.to_string())?;
        output.write_all(b"\n").map_err(|error| error.to_string())?;
        output.flush().map_err(|error| error.to_string())?;
    }
    Ok(())
}

fn print_usage() {
    eprintln!(
        "Usage:\n  price-parser '<price text>'\n  price-parser --jsonl\n\nJSONL fields: input, currency_hint, decimal_separator, digit_group_separator"
    );
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let result = if args.first().is_some_and(|arg| arg == "--jsonl") {
        run_jsonl()
    } else if args.is_empty() {
        print_usage();
        std::process::exit(2);
    } else {
        let request = ParseRequest {
            input: Some(args.join(" ")),
            currency_hint: None,
            decimal_separator: None,
            digit_group_separator: None,
        };
        execute(request).and_then(|response| {
            println!(
                "{}",
                serde_json::to_string_pretty(&response).map_err(|error| error.to_string())?
            );
            Ok(())
        })
    };

    if let Err(error) = result {
        eprintln!("price-parser: {error}");
        std::process::exit(1);
    }
}
