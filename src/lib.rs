use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
mod culidex {
    use pyo3::prelude::*;

    #[pyfunction]
    fn test_search() -> String {
        "test_ingredient".to_string()
    }
}
