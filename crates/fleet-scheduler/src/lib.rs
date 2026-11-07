#[derive(Debug, Clone)]
pub struct Robot {
    pub id: String,
    pub available: bool,
    pub battery_level: f64,
    pub distance_to_pickup: f64,
}

pub fn select_robot(robots: &[Robot]) -> Option<String> {
    robots
        .iter()
        .filter(|robot| {
            robot.available
                && robot.battery_level.is_finite()
                && robot.battery_level >= 30.0
                && robot.battery_level <= 100.0
                && robot.distance_to_pickup.is_finite()
                && robot.distance_to_pickup >= 0.0
        })
        .min_by(|a, b| {
            a.distance_to_pickup
                .total_cmp(&b.distance_to_pickup)
                .then_with(|| b.battery_level.total_cmp(&a.battery_level))
                .then_with(|| a.id.cmp(&b.id))
        })
        .map(|robot| robot.id.clone())
}

mod movement;

use pyo3::prelude::*;

/// Python-facing wrapper for the Rust scheduler.
#[pyfunction(name = "select_robot")]
fn select_robot_py(
    robots: Vec<(String, bool, f64, f64)>,
) -> Option<String> {
    let rust_robots: Vec<Robot> = robots
        .into_iter()
        .map(|(id, available, battery_level, distance_to_pickup)| Robot {
            id,
            available,
            battery_level,
            distance_to_pickup,
        })
        .collect();

    select_robot(&rust_robots)
}

/// Expose the fleet_scheduler module to Python.
#[pymodule]
fn fleet_scheduler(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(select_robot_py, m)?)?;
    m.add_function(wrap_pyfunction!(movement::shortest_path_py, m)?)?;
    m.add_function(wrap_pyfunction!(movement::sample_route_py, m)?)?;
    m.add_function(wrap_pyfunction!(movement::estimate_energy_py, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn robot(id: &str, available: bool, battery: f64, distance: f64) -> Robot {
        Robot {
            id: id.to_string(),
            available,
            battery_level: battery,
            distance_to_pickup: distance,
        }
    }

    #[test]
    fn selects_nearest_eligible_robot() {
        let robots = vec![
            robot("AMR-001", true, 85.0, 12.0),
            robot("AMR-002", true, 45.0, 5.0),
            robot("AMR-003", false, 90.0, 2.0),
        ];

        assert_eq!(select_robot(&robots), Some("AMR-002".to_string()));
    }

    #[test]
    fn excludes_robots_with_low_battery() {
        let robots = vec![
            robot("AMR-001", true, 20.0, 1.0),
            robot("AMR-002", true, 70.0, 8.0),
        ];

        assert_eq!(select_robot(&robots), Some("AMR-002".to_string()));
    }

    #[test]
    fn returns_none_without_eligible_robots() {
        let robots = vec![
            robot("AMR-001", false, 80.0, 1.0),
            robot("AMR-002", true, 10.0, 2.0),
        ];

        assert_eq!(select_robot(&robots), None);
    }

    #[test]
    fn breaks_distance_ties_using_battery() {
        let robots = vec![
            robot("AMR-001", true, 50.0, 5.0),
            robot("AMR-002", true, 80.0, 5.0),
        ];

        assert_eq!(select_robot(&robots), Some("AMR-002".to_string()));
    }

    #[test]
    fn breaks_remaining_ties_using_robot_id() {
        let robots = vec![
            robot("AMR-002", true, 80.0, 5.0),
            robot("AMR-001", true, 80.0, 5.0),
        ];

        assert_eq!(select_robot(&robots), Some("AMR-001".to_string()));
    }
}
