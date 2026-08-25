//! Rust-ядро TgTrader (crypto_core) — поиск похожих паттернов цен.
//!
//! Собирается как Python-расширение через PyO3 0.22. Python-слой вызывает
//! `find_similar_patterns_py`, передавая numpy-массивы; ядро ищет похожие
//! участки истории (косинусное сходство нормализованных окон) в параллели
//! через rayon.

use numpy::{PyArray1, PyArray2, PyArrayMethods, ToPyArray};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyDictMethods, PyList};

mod analysis;

#[pyfunction]
fn find_similar_patterns_py<'py>(
    py: Python<'py>,
    current_data: &Bound<'py, PyArray1<f64>>,
    historical_data: &Bound<'py, PyArray2<f64>>,
    window_size: usize,
    threshold: f64,
) -> PyResult<Bound<'py, PyList>> {
    let current_native = current_data.to_vec()?;
    let historical_native = historical_data.to_vec()?;

    let matcher = analysis::PatternMatcher::new(window_size, threshold);

    let results = py.allow_threads(|| {
        matcher.find_similar_patterns(
            &ndarray::Array1::from_vec(current_native),
            &ndarray::Array2::from_shape_vec(
                (historical_native.len() / window_size, window_size),
                historical_native,
            )
            .unwrap(),
        )
    });

    let list = PyList::empty_bound(py);
    for (pattern, similarity) in results {
        let dict = PyDict::new_bound(py);
        dict.set_item("pattern_type", pattern.pattern_type.to_string())?;
        dict.set_item("start_index", pattern.start_index)?;
        dict.set_item("confidence", pattern.confidence)?;
        dict.set_item("similarity", similarity)?;
        list.append(dict)?;
    }

    Ok(list)
}

/// Python модуль
#[pymodule]
fn crypto_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_similar_patterns_py, m)?)?;
    Ok(())
}
