from simulation.bond import Bond, estimate_bond_energy
from simulation.molecule import Molecule


class ReactionResult:
    def __init__(self, products: list[Molecule], energy_delta: float):
        self.products = products
        self.energy_delta = energy_delta


class Reactor:
    """Turns a handful of input molecules into product molecules plus a net
    energy delta, by procedurally breaking/forming bonds according to
    valence and electronegativity - not a fixed reaction table, and not a
    per-particle physics simulation.

    Scope is kept bounded by MAX_ATOMS_PER_REACTION and MAX_BOND_ATTEMPTS so a
    single reaction event is always cheap, regardless of world size.
    """

    MAX_ATOMS_PER_REACTION = 40
    MAX_BOND_ATTEMPTS = 50
    CATALYST_DISCOUNT = 0.5

    @staticmethod
    def react(molecules: list[Molecule], available_energy: float = 0.0, catalyzed: bool = False) -> ReactionResult:
        atoms = [atom for molecule in molecules for atom in molecule.atoms]
        bonds = [bond for molecule in molecules for bond in molecule.bonds]

        if not atoms:
            return ReactionResult([], 0.0)

        if len(atoms) > Reactor.MAX_ATOMS_PER_REACTION:
            return ReactionResult(list(molecules), 0.0)

        energy_budget = available_energy
        energy_delta = 0.0
        broken_pairs = set()

        for bond in sorted(bonds, key=lambda b: b.energy):
            break_cost = bond.energy * (Reactor.CATALYST_DISCOUNT if catalyzed else 1.0)

            if not catalyzed:
                if energy_budget < break_cost:
                    continue
                energy_budget -= break_cost

            energy_delta -= break_cost
            bond.atom_a.bonds.remove(bond)
            bond.atom_b.bonds.remove(bond)
            bonds.remove(bond)
            broken_pairs.add(frozenset((id(bond.atom_a), id(bond.atom_b))))

        attempts = 0
        while attempts < Reactor.MAX_BOND_ATTEMPTS:
            candidates = [atom for atom in atoms if atom.free_valence > 0]
            if len(candidates) < 2:
                break

            best_pair = None
            best_energy = 0.0
            for i in range(len(candidates)):
                for j in range(i + 1, len(candidates)):
                    a, b = candidates[i], candidates[j]
                    if frozenset((id(a), id(b))) in broken_pairs:
                        continue
                    if Reactor._already_bonded(a, b):
                        continue

                    energy = estimate_bond_energy(a.element, b.element, 1)
                    if energy > best_energy:
                        best_energy = energy
                        best_pair = (a, b)

            if best_pair is None:
                break

            a, b = best_pair
            bond = Bond(a, b, 1)
            a.bonds.append(bond)
            b.bonds.append(bond)
            bonds.append(bond)
            energy_delta += best_energy
            attempts += 1

        pool = Molecule()
        pool.atoms = atoms
        pool.bonds = bonds

        return ReactionResult(pool.connected_components(), energy_delta)

    @staticmethod
    def _already_bonded(a, b) -> bool:
        return any(bond.other(a) is b for bond in a.bonds)
