from simulation.models.crew import CrewState


class TestEVAPairs:
    def test_no_crew_no_eva(self):
        cs = CrewState(total_crew=0, max_pairs_per_iva=2)
        assert cs.n_eva_pairs == 0
        assert cs.n_iva_support == 0

    def test_two_crew_no_eva(self):
        cs = CrewState(total_crew=2, max_pairs_per_iva=2)
        assert cs.n_eva_pairs == 0

    def test_three_crew_one_pair(self):
        cs = CrewState(total_crew=3, max_pairs_per_iva=2)
        assert cs.n_eva_pairs == 1
        assert cs.n_iva_support == 1

    def test_five_crew_two_pairs(self):
        cs = CrewState(total_crew=5, max_pairs_per_iva=2)
        assert cs.n_eva_pairs == 2
        assert cs.n_iva_support == 1

    def test_seven_crew_default(self):
        cs = CrewState(total_crew=7, max_pairs_per_iva=2)
        assert cs.n_iva_support == 2
        assert cs.n_eva_pairs == 2

    def test_seven_crew_high_iva_ratio(self):
        cs = CrewState(total_crew=7, max_pairs_per_iva=3)
        assert cs.n_iva_support == 1
        assert cs.n_eva_pairs == 3


class TestCrewWork:
    def test_eva_hours_per_period(self):
        cs = CrewState(
            total_crew=5,
            max_pairs_per_iva=2,
            max_eva_hours_per_session=6,
            eva_days_per_period=7,
            duty_cycle=1.0,  # isolate pair/hours logic; duty cycle tested separately
        )
        # 2 EVA pairs * 6 hours/session * 7 days = 84 hours (before duty cycle)
        assert cs.eva_hours_per_period == 84

    def test_eva_hours_with_duty_cycle(self):
        cs = CrewState(
            total_crew=5,
            max_pairs_per_iva=2,
            max_eva_hours_per_session=6,
            eva_days_per_period=7,
            duty_cycle=0.6,
        )
        # 2 EVA pairs * 6 hours/session * 7 days * 0.6 duty cycle = 50.4 hours
        assert abs(cs.eva_hours_per_period - 50.4) < 0.01

    def test_no_crew_zero_hours(self):
        cs = CrewState(total_crew=0, max_pairs_per_iva=2)
        assert cs.eva_hours_per_period == 0

    def test_robotic_hours_per_period(self):
        cs = CrewState(
            total_crew=0,
            max_pairs_per_iva=2,
            n_robotic_arms=2,
            hours_per_period=168,
            robotic_time_penalty=1.5,
        )
        # 2 arms * 168 hours / 1.5 penalty = 224 effective hours
        expected = 2 * 168 / 1.5
        assert abs(cs.robotic_hours_per_period - expected) < 0.01
