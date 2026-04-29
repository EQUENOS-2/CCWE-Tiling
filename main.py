from math import ceil

from litemapy import BlockState, Entity, Region, Schematic
from nbtlib.tag import Compound, Double, List, String

schem: Schematic = Schematic.load("CCWE Parts.litematic")

OAK_LEAVES: BlockState = BlockState("minecraft:oak_leaves", persistent="true")
COMPOSTER: BlockState = BlockState("minecraft:composter")
TRAPDOOR: BlockState = BlockState("minecraft:oak_trapdoor", facing="north", open="true")

ML: Region = schem.regions["Main Logic"]
MBT: Region = schem.regions["Main Bomber Tile"]
MBT5W: Region = schem.regions["Main Bomber Tile 5w"]
MST: Region = schem.regions["Main Sweeper Tile"]
MST9W: Region = schem.regions["Main Sweeper Tile 9w"]
MST7W: Region = schem.regions["Main Sweeper Tile 7w"]
MSE: Region = schem.regions["Main Sweeper End"]

RL: Region = schem.regions["Return Logic"]
RBT: Region = schem.regions["Return Bomber Tile"]
RBT5W: Region = schem.regions["Return Bomber Tile 5w"]
RST: Region = schem.regions["Return Sweeper Tile"]
RST9W: Region = schem.regions["Return Sweeper Tile 9w"]
RST7W: Region = schem.regions["Return Sweeper Tile 7w"]
RSE: Region = schem.regions["Return Sweeper End"]


def knapsack_special_case(a: int, b: int, c: int, n: int) -> tuple[int, int, int]:
    """Given natural numbers $a, b, c, b$ finds such natural coefficients $x, y, z$ that
    the value $x a + y b + z c$ is minimal but not smaller than $n$.
    """
    k = ceil(n / a)
    best = (k * a, 0, k, 0, 0)
    max_x = n // a + 2

    for x in range(max_x + 1):
        remaining = n - x * a

        if remaining <= 0:
            total = x * a
            candidate = (total, 0, x, 0, 0)
        else:
            for y in range(remaining // b + 2):
                rem2 = remaining - y * b
                z = 0 if rem2 <= 0 else ceil(rem2 / c)
                total = x * a + y * b + z * c
                candidate = (total, y + z, x, y, z)
                if best is None or candidate < best:
                    best = candidate
            continue

        if best is None or candidate < best:
            best = candidate

    _, _, x, y, z = best
    return x, y, z


# TODO: make an actual knapsack solver and use it for both sweepers and dupers
def get_duper_counts(n: int) -> tuple[int, int]:
    k, r = divmod(n, 6)
    if r == 0:
        return k, 0
    return k + r - 5, 6 - r


def spawn_boat(x: float, y: float, z: float) -> Entity:
    data = {
        "id": String("minecraft:boat"),
        "Pos": List[Double]([Double(x), Double(y), Double(z)]),
        "Type": String("oak"),
    }
    return Entity(Compound(data))


def paste_region(
    reg1: Region, reg2: Region, offset: tuple[int, int, int] = (0, 0, 0)
) -> None:
    for x, y, z in reg2.block_positions():  # type: ignore
        reg1[x + offset[0], y + offset[1], z + offset[2]] = reg2[x, y, z]


def make_rectangle_contour(
    reg: Region, y: int, x0: int, z0: int, x1: int, z1: int
) -> None:
    for x in range(x0, x1 + 1):
        reg[x, y, z0] = OAK_LEAVES
        reg[x, y, z1] = OAK_LEAVES
    for z in range(z0, z1 + 1):
        reg[x0, y, z] = OAK_LEAVES
        reg[x1, y, z] = OAK_LEAVES


def make_outlines(width: int, length: int) -> Region:
    reg = Region(0, 0, 0, width, 1, length)
    make_rectangle_contour(reg, 0, 0, 0, width - 1, length - 1)
    make_rectangle_contour(reg, 0, 2, 11, width - 3, length - 12)
    # outline the center chunk if the size in chunks is odd x odd
    if width == length and width % 16 == 0 and (width // 16) % 2 == 1:
        x0 = z0 = (width // 16) // 2 * 16
        reg[x0, 0, z0] = reg[x0 + 1, 0, z0] = reg[x0, 0, z0 + 1] = OAK_LEAVES
        reg[x0 + 15, 0, z0] = reg[x0 + 14, 0, z0] = reg[x0 + 15, 0, z0 + 1] = OAK_LEAVES
        reg[x0, 0, z0 + 15] = reg[x0 + 1, 0, z0 + 15] = reg[x0, 0, z0 + 14] = OAK_LEAVES
        reg[x0 + 15, 0, z0 + 15] = reg[x0 + 14, 0, z0 + 15] = reg[
            x0 + 15, 0, z0 + 14
        ] = OAK_LEAVES
    return reg


class TilerDurden:  # pun intended
    def __init__(self, width: int, length: int):
        min_width = ML.width + MSE.width + MBT.width * 5
        assert width >= min_width, f"The world eater width must be at least {min_width}"
        min_len = ML.length + RL.length + 1
        assert length >= min_len, f"The world eater must be at least {min_len} long"

        self.width: int = width
        self.length: int = length
        self.duper_counts: tuple[int, int] = get_duper_counts(width - ML.width - 3)

        knapsack = lambda d: knapsack_special_case(
            MST.width, MST9W.width, MST7W.width, width - ML.width - 4 + d
        )
        self.sweeper_counts: tuple[int, int, int] = max(
            knapsack(0), knapsack(1), knapsack(2)
        )

    def make_station(
        self,
        logic: Region,
        b6w: Region,
        b5w: Region,
        s11w: Region,
        s9w: Region,
        s7w: Region,
        end: Region,
        main: bool = True,
    ) -> Region:
        if main:
            dz = dzs = 0
            dzb = logic.length - b6w.length
        else:
            dz = length - logic.length - 1
            dzs = logic.length - s11w.length
            dzb = 0

        b1, b2 = self.duper_counts
        n1, n2, n3 = self.sweeper_counts

        reg = Region(0, 1, dz, self.width, logic.height, logic.length)
        paste_region(reg, logic)
        # tile lower station
        x = logic.width
        for _ in range(n1 - 1):
            paste_region(reg, s11w, (x, 0, dzs))
            x += s11w.width
        for _ in range(n2):
            paste_region(reg, s9w, (x, 0, dzs))
            x += s9w.width
        for _ in range(n3):
            paste_region(reg, s7w, (x, 0, dzs))
            x += s7w.width
        paste_region(reg, end, (x, 0, dzs))
        # tile upper station
        x = logic.width
        for _ in range(b1):
            paste_region(reg, b6w, (x, logic.height - b6w.height, dzb))
            x += b6w.width
        x -= 1
        for _ in range(b2):
            paste_region(reg, b5w, (x, logic.height - b5w.height, dzb))
            x += b5w.width

        return reg

    def arrange_loader_spots(self, main_st: Region, sim_dist: int = 16) -> None:
        def add_loader(x, y, z):
            main_st[x, y, z] = TRAPDOOR
            main_st.entities.append(spawn_boat(x + 0.71, y, z - 0.2))

        x0, y0, z0 = 6, main_st.height - 4, 12
        width = main_st.width
        if width < 100:
            return

        snap_to_bomber = lambda x: (x - x0) // 6 * 6 + x0
        # any block that's <radius> blocks away is entity-loaded regardless of chunk alignment
        radius = sim_dist * 16
        x = snap_to_bomber(width // 2)
        if x - radius <= 0 and x + radius >= width - 1:
            return add_loader(x, y0, z0)

        max_x = snap_to_bomber(width - radius)
        x = snap_to_bomber(radius)
        n = (max_x - x) // (2 * radius)
        step = (max_x - x) // (n + 1)
        for i in range(n + 2):
            add_loader(snap_to_bomber(x + step * i), y0, z0)

    def stack_world_eater(self) -> Schematic:
        if self.width == self.length:
            suffix = f"{self.width}²"
        else:
            suffix = f"{self.width}x{self.length}"

        schem = Schematic(f"CCWE {suffix}", author="_spindle_, Aqkrm")
        main_st = self.make_station(ML, MBT, MBT5W, MST, MST9W, MST7W, MSE, main=True)
        self.arrange_loader_spots(main_st)

        schem.regions["Main"] = main_st
        schem.regions["Return"] = self.make_station(
            RL, RBT, RBT5W, RST, RST9W, RST7W, RSE, main=False
        )
        schem.regions["Outlines"] = make_outlines(self.width, self.length)
        return schem


if __name__ == "__main__":
    width, length = map(
        int, input("Enter width and length separated by a space: ").split()
    )
    tiler = TilerDurden(width, length)
    schem = tiler.stack_world_eater()
    schem.save(path := f"output/{schem.name}.litematic")
    print(f"Saved to '{path}'")
