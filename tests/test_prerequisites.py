"""
Tests for prerequisite chain logic.

Validates the 15 prerequisite chains (a-o) and ensures:
- Correct chain loading from CSV
- Proper "next in chain" logic
- Courses in multiple chains work correctly (ARIL-210, MATH-101)
- Students only see immediately next course, not courses further ahead
"""

import pytest
from logic.prerequisites import (
    load_prerequisites,
    get_chain_progress,
    is_course_eligible,
    is_next_in_chain,
    get_eligible_courses,
)


# ============================================================================
# Fixtures - Mock prerequisite data matching real CSV structure
# ============================================================================

@pytest.fixture
def prereq_data():
    """Load actual prerequisite data from CSV."""
    return load_prerequisites()


@pytest.fixture
def mock_prereq_data():
    """
    Mock prerequisite data matching the 15 chains (a-o).
    Use this for unit tests that don't need the actual CSV.
    """
    return {
        'chains': {
            'a': [(1, 'ACCT-310'), (2, 'ACCT-312'), (3, 'ACCT-313'), (4, 'ACCT-300')],
            'b': [(1, 'ARIL-210'), (2, 'ENGL-201A'), (3, 'ENGL-302A')],
            'c': [(1, 'ARIL-210'), (2, 'ENGL-311')],
            'd': [(1, 'ARIL-210'), (2, 'SOC-429')],
            'e': [(1, 'ARIL-210'), (2, 'THM-421')],
            'f': [(1, 'ECON-101'), (2, 'ECON-211'), (3, 'ECON-212')],
            'g': [(1, 'EDUC-400'), (2, 'EDUC-403'), (3, 'EDUC-407')],
            'h': [(1, 'ENGL-110'), (2, 'ENGL-120')],
            'i': [(1, 'ENGL-303'), (2, 'ENGL-301')],
            'j': [(1, 'ENGL-306'), (2, 'LIT-325')],
            'k': [(1, 'FIN-299'), (2, 'FIN-420')],
            'l': [(1, 'LAW-301'), (2, 'LAW-304')],
            'm': [(1, 'MATH-101'), (2, 'STAT-105')],
            'n': [(1, 'MATH-101'), (2, 'THM-331')],
            'o': [(1, 'THM-332'), (2, 'THM-414')],
        },
        'course_to_chains': {
            'ACCT-310': [('a', 1)],
            'ACCT-312': [('a', 2)],
            'ACCT-313': [('a', 3)],
            'ACCT-300': [('a', 4)],
            'ARIL-210': [('b', 1), ('c', 1), ('d', 1), ('e', 1)],
            'ENGL-201A': [('b', 2)],
            'ENGL-302A': [('b', 3)],
            'ENGL-311': [('c', 2)],
            'SOC-429': [('d', 2)],
            'THM-421': [('e', 2)],
            'ECON-101': [('f', 1)],
            'ECON-211': [('f', 2)],
            'ECON-212': [('f', 3)],
            'EDUC-400': [('g', 1)],
            'EDUC-403': [('g', 2)],
            'EDUC-407': [('g', 3)],
            'ENGL-110': [('h', 1)],
            'ENGL-120': [('h', 2)],
            'ENGL-303': [('i', 1)],
            'ENGL-301': [('i', 2)],
            'ENGL-306': [('j', 1)],
            'LIT-325': [('j', 2)],
            'FIN-299': [('k', 1)],
            'FIN-420': [('k', 2)],
            'LAW-301': [('l', 1)],
            'LAW-304': [('l', 2)],
            'MATH-101': [('m', 1), ('n', 1)],
            'STAT-105': [('m', 2)],
            'THM-331': [('n', 2)],
            'THM-332': [('o', 1)],
            'THM-414': [('o', 2)],
        }
    }


# ============================================================================
# Test: CSV Loading
# ============================================================================

class TestLoadPrerequisites:
    """Tests for loading prerequisite data from CSV."""

    def test_loads_all_15_chains(self, prereq_data):
        """Verify all 15 chains (a-o) are loaded."""
        chains = prereq_data['chains']
        expected_chains = set('abcdefghijklmno')
        assert set(chains.keys()) == expected_chains, f"Missing chains: {expected_chains - set(chains.keys())}"

    def test_chain_a_accounting_sequence(self, prereq_data):
        """Chain a: ACCT-310 → ACCT-312 → ACCT-313 → ACCT-300"""
        chain_a = prereq_data['chains']['a']
        assert chain_a == [
            (1, 'ACCT-310'),
            (2, 'ACCT-312'),
            (3, 'ACCT-313'),
            (4, 'ACCT-300'),
        ]

    def test_chain_f_economics_sequence(self, prereq_data):
        """Chain f: ECON-101 → ECON-211 → ECON-212"""
        chain_f = prereq_data['chains']['f']
        assert chain_f == [
            (1, 'ECON-101'),
            (2, 'ECON-211'),
            (3, 'ECON-212'),
        ]

    def test_chain_h_english_sequence(self, prereq_data):
        """Chain h: ENGL-110 → ENGL-120"""
        chain_h = prereq_data['chains']['h']
        assert chain_h == [
            (1, 'ENGL-110'),
            (2, 'ENGL-120'),
        ]

    def test_aril210_in_four_chains(self, prereq_data):
        """ARIL-210 should appear in chains b, c, d, e (all at order 1)."""
        course_to_chains = prereq_data['course_to_chains']
        aril_chains = course_to_chains.get('ARIL-210', [])

        chain_ids = {chain_id for chain_id, order in aril_chains}
        assert chain_ids == {'b', 'c', 'd', 'e'}, f"ARIL-210 chains: {chain_ids}"

        # All should be order 1
        for chain_id, order in aril_chains:
            assert order == 1, f"ARIL-210 in chain {chain_id} should be order 1, got {order}"

    def test_math101_in_two_chains(self, prereq_data):
        """MATH-101 should appear in chains m and n (both at order 1)."""
        course_to_chains = prereq_data['course_to_chains']
        math_chains = course_to_chains.get('MATH-101', [])

        chain_ids = {chain_id for chain_id, order in math_chains}
        assert chain_ids == {'m', 'n'}, f"MATH-101 chains: {chain_ids}"


# ============================================================================
# Test: Chain Progress
# ============================================================================

class TestChainProgress:
    """Tests for get_chain_progress function."""

    def test_no_courses_taken(self, mock_prereq_data):
        """Student with no courses has 0 progress in all chains."""
        progress = get_chain_progress('a', [], mock_prereq_data)
        assert progress == 0

    def test_first_course_taken(self, mock_prereq_data):
        """Student who took first course has progress of 1."""
        progress = get_chain_progress('a', ['ACCT-310'], mock_prereq_data)
        assert progress == 1

    def test_middle_of_chain(self, mock_prereq_data):
        """Student in middle of chain has correct progress."""
        courses_taken = ['ACCT-310', 'ACCT-312']
        progress = get_chain_progress('a', courses_taken, mock_prereq_data)
        assert progress == 2

    def test_completed_chain(self, mock_prereq_data):
        """Student who completed chain has max progress."""
        courses_taken = ['ACCT-310', 'ACCT-312', 'ACCT-313', 'ACCT-300']
        progress = get_chain_progress('a', courses_taken, mock_prereq_data)
        assert progress == 4

    def test_gap_in_chain(self, mock_prereq_data):
        """
        Student who skipped a course still gets max of what they took.
        Note: This tests the progress tracking, not eligibility.
        """
        # Took 1 and 3, skipped 2
        courses_taken = ['ACCT-310', 'ACCT-313']
        progress = get_chain_progress('a', courses_taken, mock_prereq_data)
        assert progress == 3  # Returns highest order taken


# ============================================================================
# Test: Course Eligibility
# ============================================================================

class TestCourseEligibility:
    """Tests for is_course_eligible function."""

    def test_first_course_always_eligible(self, mock_prereq_data):
        """First course in any chain is always eligible."""
        assert is_course_eligible('ACCT-310', [], mock_prereq_data) is True
        assert is_course_eligible('ECON-101', [], mock_prereq_data) is True
        assert is_course_eligible('ARIL-210', [], mock_prereq_data) is True

    def test_second_course_needs_first(self, mock_prereq_data):
        """Second course requires first course completed."""
        # Without prerequisite
        assert is_course_eligible('ACCT-312', [], mock_prereq_data) is False

        # With prerequisite
        assert is_course_eligible('ACCT-312', ['ACCT-310'], mock_prereq_data) is True

    def test_third_course_needs_first_two(self, mock_prereq_data):
        """Third course requires first two courses completed."""
        # Missing second course
        assert is_course_eligible('ACCT-313', ['ACCT-310'], mock_prereq_data) is False

        # Has both prerequisites
        assert is_course_eligible('ACCT-313', ['ACCT-310', 'ACCT-312'], mock_prereq_data) is True

    def test_course_not_in_chain_always_eligible(self, mock_prereq_data):
        """Courses not in any chain have no prerequisites."""
        assert is_course_eligible('BUS-101', [], mock_prereq_data) is True
        assert is_course_eligible('RANDOM-999', [], mock_prereq_data) is True


# ============================================================================
# Test: Next In Chain (Core Logic)
# ============================================================================

class TestIsNextInChain:
    """Tests for is_next_in_chain function - the core filtering logic."""

    def test_first_course_is_next_when_nothing_taken(self, mock_prereq_data):
        """First course in chain is 'next' when student hasn't taken anything."""
        assert is_next_in_chain('ACCT-310', [], mock_prereq_data) is True
        assert is_next_in_chain('ECON-101', [], mock_prereq_data) is True

    def test_second_course_is_next_after_first(self, mock_prereq_data):
        """Second course is 'next' only after first is completed."""
        # Not next yet
        assert is_next_in_chain('ACCT-312', [], mock_prereq_data) is False

        # Now it's next
        assert is_next_in_chain('ACCT-312', ['ACCT-310'], mock_prereq_data) is True

    def test_third_course_not_next_after_first(self, mock_prereq_data):
        """Third course is NOT 'next' if only first is completed."""
        # ACCT-313 requires ACCT-310 and ACCT-312 first
        assert is_next_in_chain('ACCT-313', ['ACCT-310'], mock_prereq_data) is False

    def test_third_course_is_next_after_first_two(self, mock_prereq_data):
        """Third course IS 'next' after first two completed."""
        assert is_next_in_chain('ACCT-313', ['ACCT-310', 'ACCT-312'], mock_prereq_data) is True

    def test_fourth_course_only_after_third(self, mock_prereq_data):
        """Chain a: ACCT-300 (4th) only shows after ACCT-313 (3rd)."""
        # Not yet
        assert is_next_in_chain('ACCT-300', ['ACCT-310', 'ACCT-312'], mock_prereq_data) is False

        # Now it's next
        assert is_next_in_chain('ACCT-300', ['ACCT-310', 'ACCT-312', 'ACCT-313'], mock_prereq_data) is True

    def test_course_not_in_chain_always_available(self, mock_prereq_data):
        """Courses not in any chain are always 'next'."""
        assert is_next_in_chain('BUS-101', [], mock_prereq_data) is True
        assert is_next_in_chain('BUS-101', ['ACCT-310'], mock_prereq_data) is True


# ============================================================================
# Test: Multi-Chain Courses (ARIL-210 and MATH-101)
# ============================================================================

class TestMultiChainCourses:
    """Tests for courses that appear in multiple chains."""

    def test_aril210_unlocks_four_branches(self, mock_prereq_data):
        """
        After completing ARIL-210, student can take:
        - ENGL-201A (chain b)
        - ENGL-311 (chain c)
        - SOC-429 (chain d)
        - THM-421 (chain e)
        """
        courses_taken = ['ARIL-210']

        assert is_next_in_chain('ENGL-201A', courses_taken, mock_prereq_data) is True
        assert is_next_in_chain('ENGL-311', courses_taken, mock_prereq_data) is True
        assert is_next_in_chain('SOC-429', courses_taken, mock_prereq_data) is True
        assert is_next_in_chain('THM-421', courses_taken, mock_prereq_data) is True

    def test_aril210_not_available_when_already_taken(self, mock_prereq_data):
        """ARIL-210 appears in get_eligible_courses only if not taken."""
        all_courses = ['ARIL-210', 'ENGL-201A', 'ENGL-311']

        # Not taken yet - should be eligible
        eligible = get_eligible_courses([], all_courses, mock_prereq_data)
        assert 'ARIL-210' in eligible

        # Already taken - should not appear
        eligible = get_eligible_courses(['ARIL-210'], all_courses, mock_prereq_data)
        assert 'ARIL-210' not in eligible

    def test_math101_unlocks_two_branches(self, mock_prereq_data):
        """
        After completing MATH-101, student can take:
        - STAT-105 (chain m)
        - THM-331 (chain n)
        """
        courses_taken = ['MATH-101']

        assert is_next_in_chain('STAT-105', courses_taken, mock_prereq_data) is True
        assert is_next_in_chain('THM-331', courses_taken, mock_prereq_data) is True

    def test_branch_b_progression_after_aril(self, mock_prereq_data):
        """
        Chain b: ARIL-210 → ENGL-201A → ENGL-302A
        After taking ARIL-210 and ENGL-201A, only ENGL-302A is next.
        """
        courses_taken = ['ARIL-210', 'ENGL-201A']

        # ENGL-302A is next in chain b
        assert is_next_in_chain('ENGL-302A', courses_taken, mock_prereq_data) is True

        # ENGL-311 is not next (requires only ARIL-210, which is done, so order=1+1=2)
        # Actually ENGL-311 is order 2 in chain c, and ARIL-210 is order 1
        # So after ARIL-210, ENGL-311 IS next in chain c
        assert is_next_in_chain('ENGL-311', courses_taken, mock_prereq_data) is True


# ============================================================================
# Test: Get Eligible Courses (Integration)
# ============================================================================

class TestGetEligibleCourses:
    """Integration tests for get_eligible_courses function."""

    def test_new_student_sees_first_courses(self, mock_prereq_data):
        """New student only sees first course in each chain."""
        all_required = [
            'ACCT-310', 'ACCT-312', 'ACCT-313', 'ACCT-300',  # Chain a
            'ARIL-210', 'ENGL-201A', 'ENGL-302A',  # Chain b
        ]

        eligible = get_eligible_courses([], all_required, mock_prereq_data)

        # Should see first courses only
        assert 'ACCT-310' in eligible
        assert 'ARIL-210' in eligible

        # Should NOT see later courses
        assert 'ACCT-312' not in eligible
        assert 'ACCT-313' not in eligible
        assert 'ACCT-300' not in eligible
        assert 'ENGL-201A' not in eligible

    def test_student_with_progress_sees_next_only(self, mock_prereq_data):
        """Student sees only immediately next courses, not further ahead."""
        all_required = ['ACCT-310', 'ACCT-312', 'ACCT-313', 'ACCT-300']
        courses_taken = ['ACCT-310']

        eligible = get_eligible_courses(courses_taken, all_required, mock_prereq_data)

        # ACCT-310 already taken, not shown
        assert 'ACCT-310' not in eligible

        # ACCT-312 is next
        assert 'ACCT-312' in eligible

        # ACCT-313 and ACCT-300 are NOT next yet
        assert 'ACCT-313' not in eligible
        assert 'ACCT-300' not in eligible

    def test_courses_not_in_chains_always_eligible(self, mock_prereq_data):
        """Courses without prerequisites are always eligible."""
        all_required = ['ACCT-310', 'BUS-101', 'COMP-150']

        eligible = get_eligible_courses([], all_required, mock_prereq_data)

        # First in chain
        assert 'ACCT-310' in eligible

        # No prerequisites
        assert 'BUS-101' in eligible
        assert 'COMP-150' in eligible

    def test_mixed_progress_multiple_chains(self, mock_prereq_data):
        """Student with progress in multiple chains sees correct next courses."""
        all_required = [
            'ACCT-310', 'ACCT-312', 'ACCT-313',
            'ECON-101', 'ECON-211', 'ECON-212',
            'ARIL-210', 'ENGL-201A', 'ENGL-311',
        ]
        courses_taken = ['ACCT-310', 'ECON-101', 'ECON-211']

        eligible = get_eligible_courses(courses_taken, all_required, mock_prereq_data)

        # Chain a: ACCT-312 is next
        assert 'ACCT-312' in eligible
        assert 'ACCT-313' not in eligible

        # Chain f: ECON-212 is next
        assert 'ECON-212' in eligible

        # Chains b,c: ARIL-210 not taken, so it's next
        assert 'ARIL-210' in eligible
        assert 'ENGL-201A' not in eligible
        assert 'ENGL-311' not in eligible

    def test_completed_chain_no_courses_shown(self, mock_prereq_data):
        """Student who completed a chain doesn't see those courses."""
        all_required = ['ENGL-110', 'ENGL-120']
        courses_taken = ['ENGL-110', 'ENGL-120']

        eligible = get_eligible_courses(courses_taken, all_required, mock_prereq_data)

        assert 'ENGL-110' not in eligible
        assert 'ENGL-120' not in eligible


# ============================================================================
# Test: Edge Cases
# ============================================================================

# ============================================================================
# Test: Filter Student Requirements (Integration)
# ============================================================================

class TestFilterStudentRequirements:
    """Tests for filter_student_requirements function - the main entry point."""

    @pytest.fixture
    def mock_requirements_df(self):
        """Mock requirements DataFrame matching curriculum_requirements2.csv structure."""
        import pandas as pd
        return pd.DataFrame({
            'course_code': [
                'ACCT-310', 'ACCT-312', 'ACCT-313', 'ACCT-300',  # Chain a
                'ARIL-210', 'ENGL-201A',  # Chain b
                'ECON-101', 'ECON-211',  # Chain f
                'BUS-101', 'COMP-150',  # No prerequisites
            ],
            'BAD': ['X', 'X', 'X', 'X', 'X', 'X', '', '', 'X', ''],
            'THM': ['', '', '', '', 'X', 'X', 'X', 'X', '', 'X'],
            'FIN': ['X', 'X', '', '', '', '', 'X', 'X', 'X', ''],
            'TES': ['', '', '', '', 'X', 'X', '', '', '', 'X'],
            'INT': ['X', '', '', '', '', '', '', '', 'X', 'X'],
        })

    def test_bad_major_new_student(self, mock_prereq_data, mock_requirements_df):
        """BAD major new student sees only first courses + no-prereq courses."""
        from logic.prerequisites import filter_student_requirements

        eligible = filter_student_requirements(
            student_id='12345',
            major_code='BAD-50',
            student_courses_taken=[],
            requirements_df=mock_requirements_df,
            prereq_data=mock_prereq_data
        )

        # Should see: ACCT-310 (first in chain a), ARIL-210 (first in chains b,c,d,e), BUS-101 (no prereq)
        assert 'ACCT-310' in eligible
        assert 'ARIL-210' in eligible
        assert 'BUS-101' in eligible

        # Should NOT see: later courses in chains
        assert 'ACCT-312' not in eligible
        assert 'ENGL-201A' not in eligible

    def test_bad_major_with_progress(self, mock_prereq_data, mock_requirements_df):
        """BAD major student with some progress sees correct next courses."""
        from logic.prerequisites import filter_student_requirements

        eligible = filter_student_requirements(
            student_id='12345',
            major_code='BAD-50',
            student_courses_taken=['ACCT-310', 'ARIL-210'],
            requirements_df=mock_requirements_df,
            prereq_data=mock_prereq_data
        )

        # Should see: ACCT-312 (next in chain a), ENGL-201A (next in chain b), BUS-101 (no prereq)
        assert 'ACCT-312' in eligible
        assert 'ENGL-201A' in eligible
        assert 'BUS-101' in eligible

        # Should NOT see: already taken or too far ahead
        assert 'ACCT-310' not in eligible  # Already taken
        assert 'ARIL-210' not in eligible  # Already taken
        assert 'ACCT-313' not in eligible  # Too far ahead

    def test_thm_major_student(self, mock_prereq_data, mock_requirements_df):
        """THM major student sees THM-required courses filtered by prerequisites."""
        from logic.prerequisites import filter_student_requirements

        eligible = filter_student_requirements(
            student_id='12345',
            major_code='THM-53E',
            student_courses_taken=[],
            requirements_df=mock_requirements_df,
            prereq_data=mock_prereq_data
        )

        # THM requires: ARIL-210, ENGL-201A, ECON-101, ECON-211, COMP-150
        # Eligible: ARIL-210 (first), ECON-101 (first), COMP-150 (no prereq)
        assert 'ARIL-210' in eligible
        assert 'ECON-101' in eligible
        assert 'COMP-150' in eligible

        # Not eligible yet: ENGL-201A (needs ARIL-210), ECON-211 (needs ECON-101)
        assert 'ENGL-201A' not in eligible
        assert 'ECON-211' not in eligible

    def test_invalid_major_returns_empty(self, mock_prereq_data, mock_requirements_df):
        """Invalid major code returns empty list."""
        from logic.prerequisites import filter_student_requirements

        eligible = filter_student_requirements(
            student_id='12345',
            major_code='INVALID-99',
            student_courses_taken=[],
            requirements_df=mock_requirements_df,
            prereq_data=mock_prereq_data
        )

        assert eligible == []

    def test_empty_requirements_df(self, mock_prereq_data):
        """Empty requirements DataFrame returns empty list."""
        import pandas as pd
        from logic.prerequisites import filter_student_requirements

        eligible = filter_student_requirements(
            student_id='12345',
            major_code='BAD-50',
            student_courses_taken=[],
            requirements_df=pd.DataFrame(),
            prereq_data=mock_prereq_data
        )

        assert eligible == []

    def test_all_courses_taken(self, mock_prereq_data, mock_requirements_df):
        """Student who completed all requirements gets empty list."""
        from logic.prerequisites import filter_student_requirements

        all_taken = ['ACCT-310', 'ACCT-312', 'ACCT-313', 'ACCT-300',
                     'ARIL-210', 'ENGL-201A', 'BUS-101']

        eligible = filter_student_requirements(
            student_id='12345',
            major_code='BAD-50',
            student_courses_taken=all_taken,
            requirements_df=mock_requirements_df,
            prereq_data=mock_prereq_data
        )

        assert eligible == []


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_prereq_data_returns_all(self):
        """If no prerequisite data, all required courses are eligible."""
        all_required = ['ACCT-310', 'BUS-101', 'COMP-150']
        empty_data = {'chains': {}, 'course_to_chains': {}}

        eligible = get_eligible_courses([], all_required, empty_data)
        assert eligible == all_required

    def test_none_prereq_data_returns_all(self):
        """If prereq_data is None, all required courses are eligible."""
        all_required = ['ACCT-310', 'BUS-101']

        eligible = get_eligible_courses([], all_required, None)
        assert eligible == all_required

    def test_duplicate_courses_in_list(self, mock_prereq_data):
        """Handles duplicate courses in required list."""
        all_required = ['ACCT-310', 'ACCT-310', 'ACCT-312']

        eligible = get_eligible_courses([], all_required, mock_prereq_data)

        # Should have ACCT-310 twice if it was in the input twice
        assert eligible.count('ACCT-310') == 2

    def test_empty_courses_taken(self, mock_prereq_data):
        """Empty courses_taken list works correctly."""
        all_required = ['ACCT-310', 'ACCT-312']

        eligible = get_eligible_courses([], all_required, mock_prereq_data)

        assert 'ACCT-310' in eligible
        assert 'ACCT-312' not in eligible


# ============================================================================
# Run Tests Manually (if not using pytest)
# ============================================================================

def run_manual_tests():
    """Run tests manually for debugging."""
    print("=" * 60)
    print("PREREQUISITE CHAIN TESTS")
    print("=" * 60)

    prereq_data = load_prerequisites()

    print("\n1. Loaded chains:", list(prereq_data['chains'].keys()))
    print(f"   Total chains: {len(prereq_data['chains'])}")

    print("\n2. Chain a (Accounting):")
    for order, course in prereq_data['chains'].get('a', []):
        print(f"   {order}. {course}")

    print("\n3. ARIL-210 chains:")
    for chain_id, order in prereq_data['course_to_chains'].get('ARIL-210', []):
        print(f"   Chain {chain_id}, Order {order}")

    print("\n4. MATH-101 chains:")
    for chain_id, order in prereq_data['course_to_chains'].get('MATH-101', []):
        print(f"   Chain {chain_id}, Order {order}")

    print("\n5. Testing is_next_in_chain:")

    # Test: New student
    print("   New student (no courses taken):")
    print(f"     ACCT-310 is next: {is_next_in_chain('ACCT-310', [], prereq_data)}")
    print(f"     ACCT-312 is next: {is_next_in_chain('ACCT-312', [], prereq_data)}")

    # Test: After ACCT-310
    print("   After taking ACCT-310:")
    print(f"     ACCT-312 is next: {is_next_in_chain('ACCT-312', ['ACCT-310'], prereq_data)}")
    print(f"     ACCT-313 is next: {is_next_in_chain('ACCT-313', ['ACCT-310'], prereq_data)}")

    # Test: After ARIL-210
    print("   After taking ARIL-210:")
    print(f"     ENGL-201A is next: {is_next_in_chain('ENGL-201A', ['ARIL-210'], prereq_data)}")
    print(f"     ENGL-311 is next: {is_next_in_chain('ENGL-311', ['ARIL-210'], prereq_data)}")
    print(f"     SOC-429 is next: {is_next_in_chain('SOC-429', ['ARIL-210'], prereq_data)}")
    print(f"     THM-421 is next: {is_next_in_chain('THM-421', ['ARIL-210'], prereq_data)}")

    print("\n6. Testing get_eligible_courses:")
    all_required = [
        'ACCT-310', 'ACCT-312', 'ACCT-313', 'ACCT-300',
        'ARIL-210', 'ENGL-201A', 'ENGL-302A',
        'BUS-101',  # No prerequisites
    ]

    eligible = get_eligible_courses([], all_required, prereq_data)
    print(f"   New student eligible: {eligible}")

    eligible = get_eligible_courses(['ACCT-310'], all_required, prereq_data)
    print(f"   After ACCT-310: {eligible}")

    eligible = get_eligible_courses(['ARIL-210'], all_required, prereq_data)
    print(f"   After ARIL-210: {eligible}")

    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_manual_tests()
