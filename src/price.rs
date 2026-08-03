use rust_decimal::prelude::ToPrimitive;
use rust_decimal::Decimal;

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Price {
    pub amount: Option<Decimal>,
    pub currency: Option<String>,
    pub amount_text: Option<String>,
}

impl Price {
    pub fn new(
        amount: Option<Decimal>,
        currency: Option<String>,
        amount_text: Option<String>,
    ) -> Self {
        Self {
            amount,
            currency,
            amount_text,
        }
    }

    pub fn amount_float(&self) -> Option<f64> {
        self.amount.and_then(|value| value.to_f64())
    }

    pub fn is_free(&self) -> bool {
        self.amount.is_some_and(|amount| amount.is_zero())
    }

    pub fn is_complete(&self) -> bool {
        self.amount.is_some() && self.currency.is_some()
    }
}
