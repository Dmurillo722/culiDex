use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
mod culidex {
    use pyo3::prelude::*;

    #[pyfunction]
    fn test_search() -> String {
        "test_ingredient".to_string()
    }

    #[pyfunction]
    fn cosine_scores(matrix: Vec<Vec<f64>>, query: Vec<f64>, top_n: usize) -> Vec<(usize, f64)> {
        let mut scores: Vec<(usize, f64)> = matrix
            .iter()
            .enumerate()
            .map(|(i, row)| {
                let dot: f64 = row.iter().zip(&query).map(|(a, b)| a * b).sum();
                (i, dot)
            })
            .collect();

        scores.sort_unstable_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        scores.truncate(top_n);
        scores
    }
}
