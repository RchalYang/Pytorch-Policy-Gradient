import torch
import torch.nn as nn
import torch.nn.functional as F
from utils.torch_utils import Tensor

def calc_feature_map_shape(input_shape, conv_info):
	"""
	take input shape per-layer conv-info as input
	"""
	h , w, c = input_shape
	for padding, dilation, kernel_size, stride in conv_info:
		h = int((h + 2*padding[0] - dilation[0] * ( kernel_size[0] - 1 ) - 1 ) / stride[0] + 1)
		w = int((w + 2*padding[1] - dilation[1] * ( kernel_size[1] - 1 ) - 1 ) / stride[1] + 1)
	
	return (h,w)

class MLPSharedContinuousActorCritic(nn.Module):
	def __init__(self, env,  hidden=256):

		super().__init__()

		input_size   = env.observation_space.shape[0]
		output_size  = env.action_space.shape[0]

		self.low = Tensor(env.action_space.low)
		self.high = Tensor(env.action_space.high)

		self.fc_1 = nn.Linear(input_size, hidden)
		self.fc_2 = nn.Linear(hidden, hidden)
		self.mean = nn.Linear(hidden, output_size)

		self.value = nn.Linear(hidden, 1)

		for name, para in self.named_parameters():
			if "weight" in name:
				nn.init.kaiming_normal_( para , mode='fan_out', nonlinearity='relu')
			else:
				para.data.fill_( 0 )

		self.log_std = nn.Parameter(torch.zeros(1, output_size))

		self.policy_params = [self.fc_1, self.fc_2, self.mean, self.log_std]
		
		# for param in self.parameters():
		# 	print(param)
		# print(" --------------------")
	
	def policy_parameters(self):
		for module in self.policy_params:
			# print( type( module) ) 
			if isinstance( module , nn.Parameter ):
				yield module
			elif isinstance( module , torch.Tensor ):
				yield module
			else:
				for param in module.parameters():
					yield param
	
	def forward(self, input_data):
		out = F.relu(self.fc_1(input_data))
		out = F.relu(self.fc_2(out))

		mean = self.mean(out)
		mean = torch.max(mean, self.low)
		mean = torch.min(mean, self.high)

		std = torch.exp(self.log_std)

		value = self.value(out)

		return mean, std, value


class MLPContinuousActorCritic(nn.Module):
	def __init__(self, env,  hidden=64):

		super().__init__()

		input_size   = env.observation_space.shape[0]
		output_size  = env.action_space.shape[0]

		self.low = Tensor(env.action_space.low)
		self.high = Tensor(env.action_space.high)

		self.action_1 = nn.Linear(input_size, hidden)
		self.action_2 = nn.Linear(hidden, hidden)
		self.mean = nn.Linear(hidden, output_size)

		self.value_1 = nn.Linear(input_size, hidden)
		self.value_2 = nn.Linear(hidden, hidden)
		self.value = nn.Linear(hidden, 1)

		for name, para in self.named_parameters():
			if "weight" in name:
				nn.init.kaiming_normal_( para , mode='fan_out', nonlinearity='tanh')
			else:
				para.data.fill_( 0 )

		self.log_std = nn.Parameter(torch.zeros(1, output_size))
		
		self.policy_params = [self.action_1, self.action_2, self.mean, self.log_std]
		
		# for param in self.parameters():
		# 	print(param)
		# print(" --------------------")
	
	def policy_parameters(self):
		for module in self.policy_params:
			# print( type( module) ) 
			if isinstance( module , nn.Parameter ):
				yield module
			elif isinstance( module , torch.Tensor ):
				yield module
			else:
				for param in module.parameters():
					yield param

	def forward(self, input_data):
		out = F.tanh(self.action_1(input_data))
		out = F.tanh(self.action_2(out))
		mean = self.mean(out)

		out = F.tanh(self.value_1(input_data))
		out = F.tanh(self.value_2(out))
		value = self.value(out)

		mean = torch.max(mean, self.low)
		mean = torch.min(mean, self.high)

		std = torch.exp(self.log_std)

		
		return mean, std, value


class MLPDiscreteActorCritic(nn.Module):
	def __init__(self, env, hidden=256):
		
		super().__init__()

		input_size   = env.observation_space.shape[0]
		output_size  = env.action_space.n

		self.fc_1 = nn.Linear(input_size, hidden)
		self.fc_2 = nn.Linear(hidden, hidden)

		self.action = nn.Linear(hidden, output_size)
		self.value = nn.Linear(hidden, 1)
		
		self.policy_params = [self.fc_1, self.fc_2, self.action]

		for name, para in self.named_parameters():
			if "weight" in name:
				nn.init.normal_( para )
			else:
				para.data.fill_( 0 )

	def policy_parameters(self):
		for module in self.policy_params:
			for param in module.parameters():
				yield param

	def forward(self, input_data):
		out = F.relu(self.fc_1(input_data))
		out = F.relu(self.fc_2(out))

		action = self.action(out)
		value = self.value(out)

		return action, value


class ConvDiscreteActorCritic(nn.Module):
	def __init__(self, env, hidden=256):
		super(ConvDiscreteActorCritic, self).__init__()

		input_shape = env.observation_space.shape
		output_size = env.action_space.n

		self.conv1 = nn.Conv2d( input_shape[2], 16, kernel_size=8, stride=4)
		self.conv2 = nn.Conv2d(16, 32, kernel_size=4, stride=2)

		conv_info = [
			((0,0),(1,1),(8,8),(4,4)),
			((0,0),(1,1),(4,4),(2,2)),
		]
		
		feature_map_shape = calc_feature_map_shape(input_shape, conv_info)
		
		dim_for_fc = feature_map_shape[0] * feature_map_shape[1] * 32

		
		self.fc_action = nn.Linear(dim_for_fc, hidden)
		self.action = nn.Linear(hidden, output_size)

		self.fc_value = nn.Linear(dim_for_fc, hidden)
		self.value = nn.Linear(hidden, 1)

	def forward(self, x):
		out = F.relu((self.conv1(x)))
		out = F.relu(self.conv2(out))

		out = out.view(out.size(0), -1)

		action = F.relu(self.fc_action(out))
		action = self.action(action)

		value = F.relu(self.fc_value(out))
		value = self.value(value)

		return action, value


class ConvContinuousActorCritic(nn.Module):
	def __init__(self, env, hidden=256):
		super(ConvDiscreteActorCritic, self).__init__()

		input_shape = env.observation_space.shape
		output_size = env.action_space.shape[0]

		self.conv1 = nn.Conv2d( input_shape[2], 16, kernel_size=8, stride=4)
		self.conv2 = nn.Conv2d(16, 32, kernel_size=4, stride=2)

		conv_info = [
			((0,0),(0,0),(8,8),(4,4)),
			((0,0),(0,0),(4,4),(2,2)),
		]

		feature_map_shape = calc_feature_map_shape(input_shape, conv_info)
		
		dim_for_fc = feature_map_shape[0] * feature_map_shape[1] * 32

		self.fc_action = nn.Linear(dim_for_fc, hidden)
		self.action = nn.Linear(hidden, output_size)

		self.fc_value = nn.Linear(dim_for_fc, hidden)
		self.value = nn.Linear(hidden, 1)
		
		self.log_std = nn.Parameter(torch.zeros(1, output_size))

	def forward(self, x):
		out = F.relu((self.conv1(x)))
		out = F.relu(self.conv2(out))

		out = out.view(out.size(0), -1)

		action = F.relu(self.fc_action(out))
		action = self.action(action)

		std = torch.exp(self.log_std)

		value = F.relu(self.fc_value(out))
		value = self.value(value)

		return action, std, value

class TestConv(nn.Module):
	def __init__(self, output_size):
		super(TestConv, self).__init__()

		self.conv1 = nn.Conv2d(4, 16, kernel_size=8, stride=4)
		self.conv2 = nn.Conv2d(16, 32, kernel_size=4, stride=2)
		self.fc = nn.Linear(2048, 256)
		self.head = nn.Linear(256, output_size)
		# self.softmax = nn.Softmax(dim=-1)
		
		self.value = nn.Linear(256, 1)

		self.policy_params = [self.conv1, self.conv2, self.fc, self.head]

	def policy_parameters(self):
		for module in self.policy_params:
			for param in module.parameters():
				yield param

	def forward(self, x):
		out = F.relu((self.conv1(x)))
		out = F.relu(self.conv2(out))
		out = F.relu(self.fc(out.view(out.size(0), -1)))
		# probs = self.softmax(self.head(out))
		probs = self.head(out)
		value = self.value(out)
		return probs, value
