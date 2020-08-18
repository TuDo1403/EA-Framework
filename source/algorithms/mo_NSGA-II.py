from model.GA import GA
from operators.initialization.random_initialization import RandomInitialization
from operators.crossover.simulated_binary_crossover import SBX
from operators.selection.tournament_selection import TournamentSelection
import numpy as np
from terminations.convergence import Convergence


class NSGAII(GA):
    def __init__(self,
                 pop_size=50,
                 n_offs=None,
                 initialization=RandomInitialization(),
                 selection=None,
                 crossover=SBX(),
                 elitist_archive=2,
                 **kwargs):
        super().__init__(pop_size, initialization, selection,
                         crossover, n_offs, **kwargs)
        self.default_termination = Convergence()
        self.elitist_archive = elitist_archive
        if selection is None:
            self.selection = TournamentSelection(elitist_archive)
        if n_offs is None:
            self.n_offs = self.pop_size
        
        self.CD = None
        self.F_pop = None
        self.F_offs = None
        self.ranks = {}
        self.ranks_F = {}
        self.rank = None

    def __domination_count(self, pop, F_pop):
        count = np.zeros((pop.shape[0],))
        for i, f_i in enumerate(F_pop):
            f_i_domination = [self.problem._is_dominated(f_j, f_i) for f_j in F_pop]
            count[i] = sum(f_i_domination)
        return count

    def __non_dominated_rank(self):
        pop = self.pop.copy()
        F_pop = self.F_pop.copy()
        i = 0
        ranks, ranks_F = {}, {}
        
        while len(pop) != 0:
            domination_count = self.__domination_count(pop, F_pop)
            ranks[i] = pop[domination_count == 0]
            ranks_F[i] = F_pop[domination_count == 0]
            pop = pop[domination_count != 0]
            F_pop = F_pop[domination_count != 0]
            i += 1

        return ranks, ranks_F

        

    def __non_dominated_sort(self):
        rank = np.zeros((self.ranks[0].shape[0],))
        pop = self.ranks[0]
        F_pop = self.ranks_F[0]
        n_ranks = len(self.ranks)
        for i in range(1, n_ranks):
            pop = np.vstack((pop, self.ranks[i]))
            F_pop = np.vstack((F_pop, self.ranks_F[i]))
            rank = np.concatenate((rank, np.ones(self.ranks[i].shape[0],)*i))
        
        return rank, pop, F_pop
        # for i in range(len(self.ranks)):
        #     rank.append(np.ones((self.ranks[i].shape)) * i)
        #     pop.append(self.ranks[i])
        #     F_pop.append(self.ranks_F[i])

        # return np.vstack(rank).reshape((self.pop.shape[0],)), \
        #        np.vstack(pop).reshape((self.pop.shape[0], -1)), \
        #        np.vstack(F_pop).reshape((self.pop.shape[0], -1))
    
    def __calc_crowding_distances(self, P_r):
        n = len(P_r)
        CD = np.zeros((n,))
        for obj in self.problem.objectives:
            f = np.array(list(map(obj, P_r))).flatten()
            Q = f.argsort()
            CD[Q[0]] = CD[Q[-1]] = np.inf
            for i in range(1, n-1):
                CD[Q[i]] += f[Q[i + 1]] - f[Q[i - 1]]
        return CD

    def _initialize(self):
        self.F_pop = self.evaluate(self.pop)
        self.ranks, self.ranks_F = self.__non_dominated_rank()
        self.rank, self.pop, self.F_pop = self.__non_dominated_sort()
        self.CD = np.hstack(list(map(self.__calc_crowding_distances, self.ranks.values())))
        self.fitness_pop = np.vstack((self.rank, self.CD)).T
        self.sub_tasks_each_gen()

    def _next(self):
        selected_indices = self.selection._do(self)
        self.pop = self.pop[selected_indices]
        self.F_pop = self.F_pop[selected_indices]
        # self.rank = self.rank[selected_indices]
        # self.CD = self.CD[selected_indices]
        # self.fitness_pop = self.fitness_pop[selected_indices]

        self.offs = self.crossover._do(self)
        self.F_offs = self.evaluate(self.offs)

        self.pop = np.vstack((self.pop, self.offs))
        self.F_pop = np.vstack((self.F_pop, self.F_offs))

        self.ranks, self.ranks_F = self.__non_dominated_rank()
        self.rank, self.pop, self.F_pop = self.__non_dominated_sort()
        self.CD = np.hstack(list(map(self.__calc_crowding_distances, self.ranks.values())))
        # self.CD[self.CD == np.inf] = -np.inf
        self.fitness_pop = (np.vstack((self.rank, self.CD)).T)
        sorted_idx = self.CD.argsort()[::-1]
        
        self.pop = self.pop[sorted_idx][:self.pop_size]
        self.F_pop = self.F_pop[sorted_idx][:self.pop_size]
        self.fitness_pop = self.fitness_pop[sorted_idx][:self.pop_size]

        # pop, F_pop, r = [], [], []
        # n = 0
        # for rank, f, cd in zip(self.ranks.items(), self.ranks_F.values(), self.CD):
        #     n += len(rank)
        #     sorted_cd = cd.argsort()[::-1]
        #     pop.append(rank[1][sorted_cd])
        #     F_pop.append(f[sorted_cd])
        #     r.append(np.ones((len(pop),))*rank[0])
        #     if n >= self.pop_size:
        #         break

        # self.pop = np.vstack(pop)[:self.pop_size]
        # self.F_pop = np.vstack(F_pop)[:self.pop_size]
        # self.rank = np.hstack(r)

        # pop = []
        # F_pop = []
        # for rank, rank_F in zip(self.ranks.values(), self.ranks_F.values()):
        #     if len(pop) + len(rank) > self.pop_size:
        #         n_takes = len(pop) + len(rank) - self.pop_size
        #         CD = self.__calc_crowding_distances(rank)
        #         sorted_CD = CD.argsort()[::-1]
        #         pop.append(rank[sorted_CD][:-n_takes])
        #         F_pop.append(rank_F[sorted_CD][:-n_takes])
        #         break
        #     pop.append(rank)
        #     F_pop.append(rank_F)
        # self.pop = np.vstack(pop)
        # self.F_pop = np.vstack(F_pop)

    def _save_history(self):
        res = {'P': self.pop.copy(), 
               'F': self.F_pop.copy()}
        self.history.append(res)


        

        