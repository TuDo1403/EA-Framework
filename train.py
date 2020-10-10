from agents import *
import json
from utils.flops_benchmark import add_flops_counting_methods
import torch
import numpy as np  

def print_info(self):
    n_params = np.sum(np.prod(p.size()) for p in self.parameters) / 1e6

    self.model = add_flops_counting_methods(self.model)
    self.model.eval()
    self.model.start_flops_count()
    random_data = torch.randn(1, *self.config['data_loader_args']['input_size'])
    self.model(torch.autograd.Variable(random_data).to(self.device))
    n_flops = (self.model.compute_average_flops_cost() / 1e6).round(4)

    print('{} Million of parameters\n | {} MFLOPS'.format(n_params, n_flops))

config = None
with open('./configs/train_arch.json') as  json_file:
    config = json.load(json_file)
agent_constructor = globals()[config['agent']]

agent = agent_constructor(config, callback=print_info)
agent.run()
agent.finalize()