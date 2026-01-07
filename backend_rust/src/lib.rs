use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use numpy::{PyArray1, PyArray2, ToPyArray};

mod analysis;

#[pyfunction]
fn find_similar_patterns_py(
    py: Python,
    current_data: &PyArray1<f64>,
    historical_data: &PyArray2<f64>,
    window_size: usize,
    threshold: f64,
) -> PyResult<Vec<PyObject>> {
    let current_native = current_data.as_slice()?;
    let historical_native = historical_data.as_slice()?;
    
    let matcher = analysis::PatternMatcher::new(window_size, threshold);
    
    let results = py.allow_threads(|| {
        matcher.find_similar_patterns(
            &ndarray::Array1::from_vec(current_native.to_vec()),
            &ndarray::Array2::from_shape_vec(
                (historical_native.len() / window_size, window_size),
                historical_native.to_vec()
            ).unwrap()
        )
    });
    
    // Конвертация результатов для Python
    let mut py_results = Vec::new();
    for (pattern, similarity) in results {
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("pattern_type", pattern.pattern_type.to_string())?;
        dict.set_item("start_index", pattern.start_index)?;
        dict.set_item("confidence", pattern.confidence)?;
        dict.set_item("similarity", similarity)?;
        py_results.push(dict.into());
    }
    
    Ok(py_results)
}

/// Python модуль
#[pymodule]
fn crypto_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_similar_patterns_py, m)?)?;
    Ok(())
}
