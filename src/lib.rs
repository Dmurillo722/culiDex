use pyo3::prelude::*;
use std::collections::BinaryHeap;
use std::cmp::Reverse;

#[pymodule]
mod culidex {
    use pyo3::prelude::*;
    use std::collections::BinaryHeap;
    use std::cmp::Reverse;
    use std::cmp::Ordering;

    #[derive(Debug, Clone, Copy)]
    struct ScoreEntry {
        idx : usize,
        score : f64
    }

    impl PartialEq for ScoreEntry {
        fn eq(&self, other : &Self) -> bool {
            self.score == other.score
        }
    }

    impl Eq for ScoreEntry {}

    impl PartialOrd for ScoreEntry {
        fn partial_cmp(&self, other : &Self) -> Option<std::cmp::Ordering> {
            self.score.partial_cmp(&other.score)
        }
    }

    impl Ord for ScoreEntry {
        fn cmp(&self, other : &Self) -> Ordering {
            self.partial_cmp(other).unwrap()
        }
    }
    
    #[pyfunction]
    fn test_search() -> String {
        "test_ingredient".to_string()
    }


    #[pyfunction]
    fn cosine_scores(inds : Vec<i32>, matrix : Vec<Vec<f64>>, query : Vec<f64>, top_n : usize) -> Vec<(usize, f64)> {
        let query_norm : f64 = query.iter().map(|b| b * b).sum::<f64>().sqrt();
        let mut heap: BinaryHeap<Reverse<ScoreEntry>> = BinaryHeap::with_capacity(top_n);
        

        for idx in inds {
            
            let u_idx = idx as usize;
            let Some(row) = matrix.get(u_idx) else {continue};

            let dot: f64 = row.iter().zip(&query).map(|(a, b)| a * b).sum();
            let row_norm : f64 = row.iter().map(|a| a * a).sum::<f64>().sqrt();
            let score = 
            if row_norm == 0.0 || query_norm ==0.0 {
                0.0
            } else {
                dot/(row_norm * query_norm)
            };

            let entry = ScoreEntry { idx : u_idx, score};

            if heap.len() < top_n {
                heap.push(Reverse(entry))
            } else if let Some(Reverse(min_entry)) = heap.peek() {
                if entry.score >min_entry.score {
                    heap.pop();
                    heap.push(Reverse(entry));
                }
            }

            
        }
        let mut result: Vec<(usize, f64)> = heap.into_iter().map(|Reverse(e)| (e.idx, e.score)).collect();
        result.sort_unstable_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        result
    }

   
}
