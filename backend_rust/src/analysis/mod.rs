//! Анализ исторических паттернов цен (Rust-ядро).
//!
//! Используется Python-слоем через PyO3 для быстрого поиска похожих
//! участков истории (см. lib.rs -> find_similar_patterns_py).

use ndarray::{Array1, Array2};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Pattern {
    pub pattern_type: PatternType,
    pub start_index: usize,
    pub end_index: usize,
    pub confidence: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PatternType {
    HeadAndShoulders,
    DoubleTop,
    DoubleBottom,
    Triangle,
    Flag,
    Custom(String),
}

impl PatternType {
    pub fn to_string(&self) -> String {
        match self {
            PatternType::HeadAndShoulders => "HeadAndShoulders".to_string(),
            PatternType::DoubleTop => "DoubleTop".to_string(),
            PatternType::DoubleBottom => "DoubleBottom".to_string(),
            PatternType::Triangle => "Triangle".to_string(),
            PatternType::Flag => "Flag".to_string(),
            PatternType::Custom(s) => s.clone(),
        }
    }
}

pub struct PatternMatcher {
    window_size: usize,
    similarity_threshold: f64,
    historical_patterns: Vec<Pattern>,
}

impl PatternMatcher {
    pub fn new(window_size: usize, threshold: f64) -> Self {
        Self {
            window_size,
            similarity_threshold: threshold,
            historical_patterns: Vec::new(),
        }
    }

    /// Найти похожие паттерны в исторических данных (параллельно через rayon).
    pub fn find_similar_patterns(
        &self,
        current_data: &Array1<f64>,
        historical_data: &Array2<f64>,
    ) -> Vec<(Pattern, f64)> {
        let normalized_current = self.normalize_window(current_data);

        historical_data
            .axis_chunks_iter(ndarray::Axis(0), self.window_size)
            .enumerate()
            .par_bridge()
            .filter_map(|(i, window)| {
                if window.len() < self.window_size {
                    return None;
                }

                let normalized_window = self.normalize_window(&window.row(0).to_owned());
                let similarity = self.calculate_similarity(&normalized_current, &normalized_window);

                if similarity > self.similarity_threshold {
                    let pattern = Pattern {
                        pattern_type: PatternType::Custom("historical".to_string()),
                        start_index: i,
                        end_index: i + self.window_size,
                        confidence: similarity,
                    };
                    Some((pattern, similarity))
                } else {
                    None
                }
            })
            .collect()
    }

    fn normalize_window(&self, data: &Array1<f64>) -> Array1<f64> {
        let mean = data.mean().unwrap_or(0.0);
        let std = data.std(0.0);

        if std > 0.0 {
            (data - mean) / std
        } else {
            data - mean
        }
    }

    fn calculate_similarity(&self, a: &Array1<f64>, b: &Array1<f64>) -> f64 {
        let dot_product: f64 = a.dot(b);
        let norm_a: f64 = a.dot(a).sqrt();
        let norm_b: f64 = b.dot(b).sqrt();

        if norm_a > 0.0 && norm_b > 0.0 {
            dot_product / (norm_a * norm_b)
        } else {
            0.0
        }
    }
}
