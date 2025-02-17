from __future__ import annotations

from typing import Any

from poetry.core.packages.constraints.base_constraint import BaseConstraint
from poetry.core.packages.constraints.constraint import Constraint


class MultiConstraint(BaseConstraint):
    def __init__(self, *constraints: Constraint) -> None:
        if any(c.operator == "==" for c in constraints):
            raise ValueError(
                "A multi-constraint can only be comprised of negative constraints"
            )

        self._constraints = constraints

    @property
    def constraints(self) -> tuple[Constraint, ...]:
        return self._constraints

    def allows(self, other: BaseConstraint) -> bool:
        return all(constraint.allows(other) for constraint in self._constraints)

    def allows_all(self, other: BaseConstraint) -> bool:
        if other.is_any():
            return False

        if other.is_empty():
            return True

        if not isinstance(other, MultiConstraint):
            return self.allows(other)

        our_constraints = iter(self._constraints)
        their_constraints = iter(other.constraints)
        our_constraint = next(our_constraints, None)
        their_constraint = next(their_constraints, None)

        while our_constraint and their_constraint:
            if our_constraint.allows_all(their_constraint):
                their_constraint = next(their_constraints, None)
            else:
                our_constraint = next(our_constraints, None)

        return their_constraint is None

    def allows_any(self, other: BaseConstraint) -> bool:
        if other.is_any():
            return True

        if other.is_empty():
            return True

        if isinstance(other, Constraint):
            return self.allows(other)

        if isinstance(other, MultiConstraint):
            return any(
                c1.allows(c2) for c1 in self.constraints for c2 in other.constraints
            )

        return False

    def intersect(self, other: BaseConstraint) -> BaseConstraint:
        if not isinstance(other, Constraint):
            raise ValueError("Unimplemented constraint intersection")

        constraints = self._constraints
        if other not in constraints:
            constraints += (other,)
        else:
            constraints = (other,)

        if len(constraints) == 1:
            return constraints[0]

        return MultiConstraint(*constraints)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MultiConstraint):
            return False

        return sorted(
            self._constraints, key=lambda c: (c.operator, c.version)
        ) == sorted(other.constraints, key=lambda c: (c.operator, c.version))

    def __str__(self) -> str:
        constraints = []
        for constraint in self._constraints:
            constraints.append(str(constraint))

        return ", ".join(constraints)
