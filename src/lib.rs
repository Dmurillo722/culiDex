use pyo3::prelude::*;

#[pymodule]
mod culidex {
    use pyo3::prelude::*;

    #[pyfunction]
    fn test_search() -> String {
        "test_ingredient".to_string()
    }

    #[pyfunction]
    fn cosine_scores(matrix: Vec<Vec<f64>>, query: Vec<f64>, top_n: usize) -> Vec<(usize, f64)> {
        //this version takes the raw weighted matrix, the query vector and the top_n
        //the matrix used in this version cannot be pre-normalized as different entries
        //will be used to compare different vectors based on their zero values

        let mut scores: Vec<(usize, f64)> = matrix.iter().enumerate().map(|(i, row)| {
            let dot: f64 = row.iter().zip(&query)
                .filter(|(a, b)| **a != 0.0 && **b != 0.0)
                .map(|(a, b)| a * b)
                .sum();

            let row_norm: f64 = row.iter().zip(&query)
                .filter(|(a, b)| **a != 0.0 && **b != 0.0)
                .map(|(a, _)| a * a)
                .sum::<f64>()
                .sqrt();

            let query_norm: f64 = row.iter().zip(&query)
                .filter(|(a, b)| **a != 0.0 && **b != 0.0)
                .map(|(_, b)| b * b)
                .sum::<f64>()
                .sqrt();

            let score = if row_norm == 0.0 || query_norm == 0.0 { 0.0 }
                        else { dot / (row_norm * query_norm) };
            (i, score)
        }).collect();

        scores.sort_unstable_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        scores.truncate(top_n);
        scores
    }
}
