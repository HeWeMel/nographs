""" Functionality that ease the handling of a calculation limit in a strategy. """

from tpl.make_insert_look_defined import *

# """$$


class MCalculationLimit:
    """Methods to ease implementing the handling of the calculation limit."""

    @staticmethod
    def prepare():
        insert(
            f"""\
            # Prepare limit check done by zero check
            if calculation_limit is not None:
                calculation_limit += 1

"""
        )

    @staticmethod
    def step(reduction_value: str = ""):
        if reduction_value:
            insert(
                f"""\
                if calculation_limit is not None and calculation_limit >= 0:
                    if (
                            calculation_limit := calculation_limit - {reduction_value}
                    ) < 0:
                        raise RuntimeError("Number of visited vertices reached limit")
"""
            )
        else:
            insert(
                f"""\
                if calculation_limit and not (
                    calculation_limit := calculation_limit - 1
                ):
                    raise RuntimeError("Number of visited vertices reached limit")
"""
            )


# $$"""
