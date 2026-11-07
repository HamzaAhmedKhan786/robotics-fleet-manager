//! Deterministic warehouse routing and coordinate sampling.
//! Coordinates are display-world units, not physical robot telemetry.
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::collections::{BTreeMap, BTreeSet};

const EPS: f64 = 1e-9;

fn valid_number(value: f64) -> bool {
    value.is_finite() && value >= 0.0
}

pub fn route(
    edges: &[(String, String, f64)],
    start: &str,
    goal: &str,
) -> Result<Option<(Vec<String>, f64)>, String> {
    let mut graph: BTreeMap<String, Vec<(String, f64)>> = BTreeMap::new();
    for (a, b, weight) in edges {
        if a.is_empty() || b.is_empty() || !valid_number(*weight) {
            return Err("Invalid warehouse edge".into());
        }
        graph.entry(a.clone()).or_default().push((b.clone(), *weight));
        graph.entry(b.clone()).or_default();
    }
    if start == goal {
        return Ok(Some((vec![start.into()], 0.0)));
    }
    if !graph.contains_key(start) || !graph.contains_key(goal) {
        return Ok(None);
    }

    let mut remaining: BTreeSet<String> = graph.keys().cloned().collect();
    let mut costs: BTreeMap<String, f64> = BTreeMap::new();
    let mut previous: BTreeMap<String, String> = BTreeMap::new();
    costs.insert(start.into(), 0.0);
    while !remaining.is_empty() {
        let current = remaining.iter()
            .min_by(|a, b| {
                costs.get(*a).copied().unwrap_or(f64::INFINITY)
                    .total_cmp(&costs.get(*b).copied().unwrap_or(f64::INFINITY))
                    .then_with(|| a.cmp(b))
            }).cloned().expect("nonempty set");
        let current_cost = costs.get(&current).copied().unwrap_or(f64::INFINITY);
        if !current_cost.is_finite() { break; }
        if current == goal { break; }
        remaining.remove(&current);
        if let Some(neighbors) = graph.get(&current) {
            for (neighbor, weight) in neighbors {
                if !remaining.contains(neighbor) { continue; }
                let candidate = current_cost + weight;
                let existing = costs.get(neighbor).copied().unwrap_or(f64::INFINITY);
                if candidate + EPS < existing {
                    costs.insert(neighbor.clone(), candidate);
                    previous.insert(neighbor.clone(), current.clone());
                }
            }
        }
    }
    let Some(total) = costs.get(goal).copied() else { return Ok(None); };
    let mut path = vec![goal.into()];
    while path.last().is_some_and(|p| p != start) {
        let Some(parent) = previous.get(path.last().unwrap()) else { return Ok(None); };
        path.push(parent.clone());
    }
    path.reverse();
    Ok(Some((path, total)))
}

pub fn sample(points: &[(f64, f64)], elapsed: f64, duration: f64) -> Result<(f64, f64, f64), String> {
    if points.is_empty() || !elapsed.is_finite() || !duration.is_finite() || duration <= 0.0
        || points.iter().any(|(x, z)| !x.is_finite() || !z.is_finite()) {
        return Err("Invalid route or time".into());
    }
    let progress = (elapsed / duration).clamp(0.0, 1.0);
    if points.len() == 1 { return Ok((points[0].0, points[0].1, progress)); }
    let total: f64 = points.windows(2).map(|p| (p[1].0 - p[0].0).hypot(p[1].1 - p[0].1)).sum();
    if total <= EPS { return Ok((points[0].0, points[0].1, progress)); }
    let mut remaining = progress * total;
    for pair in points.windows(2) {
        let segment = (pair[1].0 - pair[0].0).hypot(pair[1].1 - pair[0].1);
        if remaining <= segment || pair[1] == *points.last().unwrap() {
            let t = if segment <= EPS { 0.0 } else { (remaining / segment).clamp(0.0, 1.0) };
            return Ok((pair[0].0 + (pair[1].0 - pair[0].0) * t,
                       pair[0].1 + (pair[1].1 - pair[0].1) * t, progress));
        }
        remaining -= segment;
    }
    let last = points[points.len()-1];
    Ok((last.0, last.1, progress))
}

#[pyfunction(name = "shortest_path")]
pub fn shortest_path_py(
    edges: Vec<(String, String, f64)>, start: String, goal: String,
) -> PyResult<Option<(Vec<String>, f64)>> {
    route(&edges, &start, &goal).map_err(PyValueError::new_err)
}

#[pyfunction(name = "sample_route")]
pub fn sample_route_py(
    points: Vec<(f64, f64)>, elapsed_seconds: f64, duration_seconds: f64,
) -> PyResult<(f64, f64, f64)> {
    sample(&points, elapsed_seconds, duration_seconds).map_err(PyValueError::new_err)
}

#[pyfunction(name = "estimate_energy")]
pub fn estimate_energy_py(distance: f64, percent_per_unit: f64) -> PyResult<f64> {
    if !valid_number(distance) || !valid_number(percent_per_unit) {
        return Err(PyValueError::new_err("Invalid distance or energy rate"));
    }
    Ok((distance * percent_per_unit * 100.0).round() / 100.0)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn finds_shortest_route() {
        let edges = vec![("A".into(), "B".into(), 3.0), ("B".into(), "C".into(), 4.0), ("A".into(), "C".into(), 10.0)];
        assert_eq!(route(&edges, "A", "C").unwrap(), Some((vec!["A".into(), "B".into(), "C".into()], 7.0)));
    }
    #[test]
    fn respects_unreachable_and_invalid_weights() {
        assert_eq!(route(&[], "A", "B").unwrap(), None);
        assert!(route(&[("A".into(), "B".into(), -1.0)], "A", "B").is_err());
    }
    #[test]
    fn samples_movement_and_clamps() {
        let path = vec![(0.0, 0.0), (6.0, 0.0), (6.0, 4.0)];
        assert_eq!(sample(&path, 5.0, 10.0).unwrap(), (5.0, 0.0, 0.5));
        assert_eq!(sample(&path, 20.0, 10.0).unwrap(), (6.0, 4.0, 1.0));
    }
    #[test]
    fn estimates_energy_and_rejects_invalid_input() {
        assert_eq!(estimate_energy_py(28.0, 0.35).unwrap(), 9.8);
        assert!(estimate_energy_py(-1.0, 0.35).is_err());
    }
    #[test]
    fn validates_samples() {
        assert!(sample(&[], 1.0, 10.0).is_err());
        assert!(sample(&[(0.0, 0.0)], 1.0, 0.0).is_err());
    }
}
