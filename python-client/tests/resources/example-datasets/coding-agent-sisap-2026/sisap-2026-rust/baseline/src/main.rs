// Exact (brute-force, dot product) baseline of the SISAP 2026 Indexing Challenge (tasks 1, 2, and 3) in Rust.
//
// Usage: sisap2026 --input <file.h5> --task-description <config.json> --output <dir>
use hdf5_metno as hdf5;
use ndarray::Array2;
use rayon::prelude::*;
use std::collections::HashMap;
use std::time::Instant;

struct Sparse {
    data: Vec<f32>,
    indices: Vec<usize>,
    indptr: Vec<usize>,
    dim: usize,
}

impl Sparse {
    fn rows(&self) -> usize {
        self.indptr.len() - 1
    }
    fn row(&self, i: usize) -> (&[usize], &[f32]) {
        let (a, b) = (self.indptr[i], self.indptr[i + 1]);
        (&self.indices[a..b], &self.data[a..b])
    }
}

fn read_sparse(file: &hdf5::File, group: &str) -> hdf5::Result<Sparse> {
    let g = file.group(group)?;
    let shape: Vec<i64> = g.attr("shape")?.read_raw()?;
    let indptr = g.dataset("indptr")?;
    let indptr: Vec<usize> = match indptr.read_raw::<i64>() {
        Ok(v) => v.into_iter().map(|i| i as usize).collect(),
        Err(_) => indptr.read_raw::<i32>()?.into_iter().map(|i| i as usize).collect(),
    };
    Ok(Sparse {
        data: g.dataset("data")?.read_raw()?,
        indices: g.dataset("indices")?.read_raw::<i32>()?.into_iter().map(|i| i as usize).collect(),
        indptr,
        dim: shape[1] as usize,
    })
}

// The identifiers (1-based) and the dot-product scores of the k highest-scoring entries, best first
fn top_k(scores: &[f32], k: usize, skip: Option<usize>) -> (Vec<i32>, Vec<f32>) {
    let mut ids: Vec<usize> = (0..scores.len()).filter(|i| Some(*i) != skip).collect();
    let cmp = |a: &usize, b: &usize| scores[*b].total_cmp(&scores[*a]);
    ids.select_nth_unstable_by(k - 1, cmp);
    ids.truncate(k);
    ids.sort_by(cmp);
    (ids.iter().map(|i| *i as i32 + 1).collect(), ids.iter().map(|i| scores[*i]).collect())
}

fn collect(results: Vec<(Vec<i32>, Vec<f32>)>, k: usize) -> (Array2<i32>, Array2<f32>) {
    let n = results.len();
    let knns = Array2::from_shape_vec((n, k), results.iter().flat_map(|r| r.0.clone()).collect()).unwrap();
    let dists = Array2::from_shape_vec((n, k), results.iter().flat_map(|r| r.1.clone()).collect()).unwrap();
    (knns, dists)
}

fn dense_search(db: &Array2<f32>, queries: &Array2<f32>, k: usize, exclude_self: bool) -> (Array2<i32>, Array2<f32>) {
    let results: Vec<_> = (0..queries.nrows())
        .into_par_iter()
        .map(|i| {
            let scores: Vec<f32> = db.rows().into_iter().map(|r| r.dot(&queries.row(i))).collect();
            top_k(&scores, k, if exclude_self { Some(i) } else { None })
        })
        .collect();
    collect(results, k)
}

fn sparse_search(db: &Sparse, queries: &Sparse, k: usize) -> (Array2<i32>, Array2<f32>) {
    let results: Vec<_> = (0..queries.rows())
        .into_par_iter()
        .map(|q| {
            let (qi, qv) = queries.row(q);
            let mut dense = vec![0f32; queries.dim.max(db.dim)];
            qi.iter().zip(qv).for_each(|(i, v)| dense[*i] = *v);
            let scores: Vec<f32> = (0..db.rows())
                .map(|d| {
                    let (di, dv) = db.row(d);
                    di.iter().zip(dv).map(|(i, v)| dense[*i] * v).sum()
                })
                .collect();
            top_k(&scores, k, None)
        })
        .collect();
    collect(results, k)
}

fn save_results(path: &str, knns: &Array2<i32>, dists: &Array2<f32>, attrs: &[(&str, String)]) -> hdf5::Result<()> {
    let file = hdf5::File::create(path)?;
    file.new_dataset_builder().with_data(knns).create("knns")?;
    file.new_dataset_builder().with_data(dists).create("dists")?;
    for (key, value) in attrs {
        let v: hdf5::types::VarLenUnicode = value.parse().unwrap();
        file.new_attr::<hdf5::types::VarLenUnicode>().create(*key)?.write_scalar(&v)?;
    }
    Ok(())
}

fn main() -> hdf5::Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let options: HashMap<&str, &str> = args.chunks(2).map(|c| (c[0].as_str(), c[1].as_str())).collect();
    let cfg: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(options["--task-description"]).unwrap()).unwrap();
    let (task, k) = (cfg["task"].as_str().unwrap(), cfg["k"].as_u64().unwrap() as usize);
    let (data, queries) = (cfg["data"].as_str().unwrap(), cfg["queries"].as_str());
    let file = hdf5::File::open(options["--input"])?;

    let start = Instant::now();
    let (knns, dists) = match task {
        "task1" => {
            let x: Array2<f32> = file.dataset(data)?.read_2d()?;
            // the object itself is excluded from its neighbors
            dense_search(&x, &x, k, true)
        }
        "task2" => {
            let x: Array2<f32> = file.dataset(data)?.read_2d()?;
            let q: Array2<f32> = file.dataset(queries.unwrap())?.read_2d()?;
            dense_search(&x, &q, k, false)
        }
        "task3" => sparse_search(&read_sparse(&file, data)?, &read_sparse(&file, queries.unwrap())?, k),
        other => panic!("unknown task {other}"),
    };
    let querytime = start.elapsed().as_secs_f64();

    std::fs::create_dir_all(options["--output"]).map_err(|e| e.to_string())?;
    let attrs = [
        ("algo", "BruteForce".to_string()),
        ("params", "exact inner product".to_string()),
        ("buildtime", "0.0".to_string()),
        ("querytime", querytime.to_string()),
        ("task", task.to_string()),
        ("dataset", cfg["dataset_name"].as_str().unwrap_or("").to_string()),
    ];
    save_results(&format!("{}/results-1-BruteForce.h5", options["--output"]), &knns, &dists, &attrs)
}
