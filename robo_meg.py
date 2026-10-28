"""
Модуль роботизированного мегалодона RoboMeg.
"""

from typing import Any, Dict, Set


class CrazyVehicleError(RuntimeError):
    """Базовое исключение для безумных транспортных средств."""
    pass


class RoboMegError(CrazyVehicleError):
    """Базовое исключение для RoboMeg."""
    pass


class EnergyEmpty(RoboMegError):
    """Выбрасывается при нехватке энергии для совершения манёвра."""
    pass


class RoboMegCannotMoveOnGround(RoboMegError):
    """Выбрасывается при попытке передвижения по земле."""
    pass


class AlreadyAirborne(RoboMegError):
    """Выбрасывается при попытке совершить прыжок из воздуха."""
    pass


class JumpTooLong(RoboMegError):
    """Выбрасывается при попытке прыжка на расстояние больше jump_length_km."""
    pass


class RoboMegNotHungry(RoboMegError):
    """Выбрасывается при попытке охоты, когда уровень энергии 50 и выше."""
    pass


class UnsafeHuntingZone(RoboMegError):
    """Выбрасывается при охоте в воздухе или до преодоления 2 км в воде после старта/прыжка."""
    pass


class NoFishHere(RoboMegError):
    """Выбрасывается при повторной охоте на уже выловленной координате position_km."""
    pass


class RoboMeg:
    """
    Класс автономного биомеханического подводного аппарата «RoboMeg».
    """

    HUNT_CIRCLE_DIAMETER_KM: float = 2.0
    HUNT_ENERGY_GAIN: float = 20.0
    EPSILON: float = 1e-6

    def __init__(
        self,
        name: str,
        mass_kg: float,
        jump_length_km: float,
        bite_force_kn: float,
        max_speed_kmh: float,
        energy: float = 100.0,
    ) -> None:
        # Проверка типов параметров
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if isinstance(name, str) and not name.strip():
            raise ValueError("name must not be empty")

        for param_name, param_val in [
            ("mass_kg", mass_kg),
            ("jump_length_km", jump_length_km),
            ("bite_force_kn", bite_force_kn),
            ("max_speed_kmh", max_speed_kmh),
        ]:
            if isinstance(param_val, bool) or not isinstance(param_val, (int, float)):
                raise TypeError(f"{param_name} must be a number")
            if param_val <= 0:
                raise ValueError(f"{param_name} must be positive")

        if isinstance(energy, bool) or not isinstance(energy, (int, float)):
            raise TypeError("energy must be a number")
        if not (0.0 <= energy <= 100.0):
            raise ValueError("energy must be between 0 and 100")

        self._name: str = name
        self._mass_kg: float = float(mass_kg)
        self._jump_length_km: float = float(jump_length_km)
        self._bite_force_kn: float = float(bite_force_kn)
        self._max_speed_kmh: float = float(max_speed_kmh)
        self._energy: float = round(float(energy), 6)

        self._position_km: float = 0.0
        self._is_airborne: bool = False

        # Внутреннее состояние:
        # Счётчик проплытой дистанции в воде после старта / последнего прыжка
        self._swum_in_water_since_jump_km: float = 0.0
        # Множество координат position_km, на которых уже проводилась охота
        self._hunted_positions: Set[float] = set()

    @property
    def name(self) -> str:
        """Имя транспорта."""
        return self._name

    @property
    def mass_kg(self) -> float:
        """Масса аппарата в кг."""
        return self._mass_kg

    @property
    def jump_length_km(self) -> float:
        """Максимальная длина одного прыжка по воздуху в км."""
        return self._jump_length_km

    @property
    def bite_force_kn(self) -> float:
        """Сила сжатия челюстей в кН."""
        return self._bite_force_kn

    @property
    def max_speed_kmh(self) -> float:
        """Максимальная скорость в воде в км/ч."""
        return self._max_speed_kmh

    @property
    def energy(self) -> float:
        """Текущий запас энергии."""
        return self._energy

    @property
    def position_km(self) -> float:
        """Пройденное расстояние по маршруту в км."""
        return self._position_km

    @property
    def is_airborne(self) -> bool:
        """Находится ли аппарат в фазе прыжка в воздухе."""
        return self._is_airborne

    def move(self, distance_km: float, terrain: str) -> float:
        """
        Перемещает мегалодон на заданное расстояние в указанной среде.
        """
        if isinstance(distance_km, bool) or not isinstance(distance_km, (int, float)):
            raise TypeError("distance_km must be a number")
        if distance_km <= 0:
            raise ValueError("distance_km must be positive")

        if not isinstance(terrain, str):
            raise TypeError("terrain must be a string")
        if terrain not in ("water", "air", "ground"):
            raise ValueError(f"unknown terrain: {terrain}")

        if terrain == "ground":
            raise RoboMegCannotMoveOnGround("robomeg cannot move on ground")

        if terrain == "air":
            if self._is_airborne:
                raise AlreadyAirborne("cannot jump while already airborne")
            if distance_km > self._jump_length_km:
                raise JumpTooLong("jump distance exceeds max jump length")

            energy_needed = round(distance_km * 2.0, 6)
            if self._energy + self.EPSILON < energy_needed:
                raise EnergyEmpty("not enough energy")

            time_hours = round(distance_km / (self._max_speed_kmh * 2.0), 6)
            new_energy = max(0.0, round(self._energy - energy_needed, 6))
            new_pos = round(self._position_km + distance_km, 6)

            self._energy = new_energy
            self._position_km = new_pos
            self._is_airborne = True
            self._swum_in_water_since_jump_km = 0.0
            return time_hours

        # terrain == "water"
        energy_needed = round(distance_km * 1.0, 6)
        if self._energy + self.EPSILON < energy_needed:
            raise EnergyEmpty("not enough energy")

        time_hours = round(distance_km / self._max_speed_kmh, 6)
        new_energy = max(0.0, round(self._energy - energy_needed, 6))
        new_pos = round(self._position_km + distance_km, 6)

        self._energy = new_energy
        self._position_km = new_pos
        self._is_airborne = False
        self._swum_in_water_since_jump_km = round(
            self._swum_in_water_since_jump_km + distance_km, 6
        )
        return time_hours

    def pass_island(self, diameter_km: float) -> float:
        """
        Преодолевает встреченный на пути остров оптимальным способом.
        """
        if isinstance(diameter_km, bool) or not isinstance(diameter_km, (int, float)):
            raise TypeError("diameter_km must be a number")
        if diameter_km <= 0:
            raise ValueError("diameter_km must be positive")

        if diameter_km <= self._jump_length_km:
            return self.move(diameter_km, "air")

        arc_km = round(1.5 * diameter_km, 6)
        return self.move(arc_km, "water")

    def hunt_fish(self) -> None:
        """
        Восполняет энергию на 20 единиц путём совершения кормового круга.
        Строгий приоритет проверок:
        1. UnsafeHuntingZone (в воздухе или проплыто < 2.0 км по воде после старта/прыжка)
        2. NoFishHere (на текущей position_km уже проводилась охота)
        3. RoboMegNotHungry (energy >= 50.0)
        """
        if self._is_airborne or self._swum_in_water_since_jump_km < 2.0:
            raise UnsafeHuntingZone("must swim at least 2.0 km in water before hunting")

        if self._position_km in self._hunted_positions:
            raise NoFishHere("fish already eaten at position")

        if self._energy >= 50.0:
            raise RoboMegNotHungry("energy is 50 or above, hunting is not needed")

        self._energy = min(100.0, round(self._energy + self.HUNT_ENERGY_GAIN, 6))
        self._hunted_positions.add(self._position_km)

    def can_overcome(self, obstacle: str) -> bool:
        """
        Проверяет возможность преодоления морского препятствия без изменения состояния.
        """
        if not isinstance(obstacle, str):
            raise TypeError("obstacle must be a string")

        if obstacle == "coral_reef":
            return self._is_airborne is True
        elif obstacle == "iceberg":
            return self._bite_force_kn > 50.0 and self._energy > 30.0
        elif obstacle == "steel_net":
            return self._is_airborne is True or self._bite_force_kn > 25.0
        elif obstacle == "whirlpool":
            return (
                self._is_airborne is False
                and self._max_speed_kmh >= 60.0
                and self._energy > 40.0
            )
        else:
            raise ValueError(f"unknown obstacle: {obstacle}")

    def calculate_energy(self, distance_km: float, terrain: str) -> float:
        """
        Расчёт затрат энергии без изменения состояния.
        """
        if isinstance(distance_km, bool) or not isinstance(distance_km, (int, float)):
            raise TypeError("distance_km must be a number")
        if distance_km <= 0:
            raise ValueError("distance_km must be positive")

        if not isinstance(terrain, str):
            raise TypeError("terrain must be a string")

        if terrain == "ground":
            raise RoboMegCannotMoveOnGround("robomeg cannot move on ground")
        elif terrain == "water":
            return round(distance_km * 1.0, 6)
        elif terrain == "air":
            return round(distance_km * 2.0, 6)
        else:
            raise ValueError(f"unknown terrain: {terrain}")

    def refuel(self, amount: float) -> None:
        """
        Пополнение энергии до максимума 100.0.
        """
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise TypeError("amount must be a number")
        if amount <= 0:
            raise ValueError("amount must be positive")

        self._energy = min(100.0, round(self._energy + amount, 6))

    def get_status(self) -> Dict[str, Any]:
        """
        Возвращает снимок всех публичных атрибутов в виде словаря.
        """
        return {
            "name": self._name,
            "mass_kg": self._mass_kg,
            "jump_length_km": self._jump_length_km,
            "bite_force_kn": self._bite_force_kn,
            "max_speed_kmh": self._max_speed_kmh,
            "energy": self._energy,
            "position_km": self._position_km,
            "is_airborne": self._is_airborne,
        }
