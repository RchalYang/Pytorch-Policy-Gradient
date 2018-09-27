import argparse

def get_args():
	parser = argparse.ArgumentParser( formatter_class=argparse.ArgumentDefaultsHelpFormatter )
	#
	parser.add_argument('--save_interval',help="save model interval",           type=int,   default=200)
	parser.add_argument('--resume',       help="whether to resume",             action="store_true", default=False)
	parser.add_argument('--share_para',   help="whether to share param",        type=bool, default=True)
	parser.add_argument("--max_iter",     help="max iteration for algorithems", type=int, default=5000 )
	#Agent
	parser.add_argument('--agent',        help='agent name',                    default='PPO')
	#Universal Setting
	parser.add_argument('--env',          help='environment ID',                default='PongNoFrameskip-v4')
	parser.add_argument("--rllr",         help="rl learning rate",              type=float, default=1e-3)
	parser.add_argument("--gamma",        help="discount factor",               type=float, default=0.98)
	parser.add_argument("--episodes",     help="episodes generated every time", type=int,   default=1)
	parser.add_argument("--entropy_para", help="entropy coefficient ",          type=float, default=0.01)
	parser.add_argument("--batch_size",   help="batch size",                    type=int,   default=4096)
	parser.add_argument("--tau",          help="tau for soft update",           type=float, default=1.0 )
	#TRPO
	parser.add_argument("--max_kl",       help="max KL divergence", type=float, default=0.001)
	parser.add_argument("--cg_damping",   help="damping factor for conjugate gradient", type=float, default=0.001)
	parser.add_argument("--cg_iters",     help="num of iterations for conjugate gradient", type=int, default=10)
	parser.add_argument("--residual_tol", help="residual tolerance", type=float, default=1e-10)
	#PPO
	parser.add_argument("--update_time", help = "update num for ppo", type = int, default=5 )
	parser.add_argument("--clip_para",   help = "clip_para for ppo", type = float, default=0.2 )
	#A3C
	parser.add_argument("--num_workers", help = "num of workers for a3c", type = int, default=4 )

	args = parser.parse_args()
	return args