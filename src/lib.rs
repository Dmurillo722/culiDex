use pyo3::prelude::*;

#[pymodule]
mod culidex {
    use pyo3::prelude::*;

    #[pyfunction]
    fn test_search() -> String {
        "test_ingredient".to_string()
    }
    #[pyfunction]
    fn cosine_scores(inds : Vec<i32>, matrix : Vec<Vec<f64>>, query : Vec<f64>, top_n : usize) -> Vec<(usize, f64)> {
        
        let query_norm : f64 = query.iter().map(|b| b * b).sum::<f64>().sqrt();

        let mut scores :  Vec<(usize, f64)> = inds
        .into_iter()
        .filter_map(|idx| {
            let u_idx = idx as usize;
            matrix.get(u_idx).map(|row| (u_idx, row))
        })
        .map(|(i, row)| {
            let dot : f64 = row.iter().zip(&query).map(|(a,b)| a * b).sum();
            let row_norm : f64 = row.iter().map(|a| a * a).sum::<f64>().sqrt();

            let score = 
            if row_norm == 0.0 || query_norm ==0.0 {
                0.0
            } else {
                dot/(row_norm * query_norm)
            };

            (i, score)
        }).collect();
        
        scores.sort_unstable_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        scores.truncate(top_n);
        scores
  
    }

}
