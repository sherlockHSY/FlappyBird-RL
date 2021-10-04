import random
import pandas as pd

class QLearning(object):
    def __init__(self, action_space, capacity=100000, learning_rate=0.7, reward_decay=0.95, e_greedy=0.9):
        super().__init__()
        self.lr_decay = 0.00003
        self.gamma = reward_decay # discount factor 折扣因子
        self.lr = learning_rate
        self.epsilon = e_greedy
        self.action_space = action_space
        self.capacity = capacity
        self.history_moves = []
        self.q_table = {}

    
    def check_state_exit(self, state):
        if state != 'terminal':
            if self.q_table.get(state) is None:
                self.q_table[state] = [0,0]


    def choose_action(self, state):
 
        self.check_state_exit(state)
        
        state_action = self.q_table[state]

        # 在这个游戏场景下，选择动作为1 即小鸟往上飞的情况并不需要很多，所以当两个动作的价值相同时，我们更倾向于选择 0 动作
        # In this environment, we are more inclined to choose action 0
        action = 0 if state_action[0]>=state_action[1] else 1

        # Eplsion-greedy的方法在这个环境下并不适用，该环境下不需要过多的探索
        # Eplsion-greedy is not efficient or required for this agent and environment 
        # if random.random() < self.epsilon:
        #     # 选取Q值最大的动作，但当出现相同Q值的动作时，需在这些动作中随机选择
        #     if len(state_action.index(max(state_action))) == 1 :
        #         action = state_action.index(max(state_action))[0]
        #     else:
        #         # 但在这个游戏中，明显 0 动作要比 1 动作 更普遍，我们更倾向于选择0
        #         action = 0 if random.random()>0.1 else 1
        # else:
        #     # choose random action
        #     action = random.choice(self.action_space)
        # self.
        
        return action
        
    # 更新Q表 Update Q-table
    def learn(self, s, a, r, s_,done):
        
        self.check_state_exit(s_)
        self.history_moves.append({
            "s": s,
            "a": a,
            "r": r,
            "s_": s_
        })
        
        # 正常单步更新 Q-learing is Single-step update
        if s_ != 'terminal':
            q_target = r + self.gamma * max(self.q_table[s_][0:2])
        else:
            q_target = r
        
        self.q_table[s][a] = (1 - self.lr) * (self.q_table[s][a]) + \
                                                self.lr * (q_target)

        # 结束一局游戏后，额外更新Q表 Additional update of Q-table
        if done:
            history = list(reversed(self.history_moves))
            # 小鸟如果撞到的是上方的障碍物，就让它最后的两个状态不要往上飞
            # Flag if the bird died in the top pipe, don't flap if this is the case
            high_death_flag = True if int(s.split("_")[1]) > 120 else False
            t, last_flap = 0, True
            
            for move in history:
                t += 1
                update_s,update_a, update_r,upadte_s_ = move["s"],move["a"],move["r"],move["s_"]
                if t <=2 :
                    if t==2:
                        update_r = -1000
                        move["r"] = -1000
                        self.q_table[update_s][update_a] = (1 - self.lr) * (self.q_table[update_s][update_a]) + \
                                                    self.lr * (update_r + self.gamma *
                                                                    max(self.q_table[upadte_s_][0:2]))
                    if update_a:
                        last_flap = False

                elif (last_flap or high_death_flag) and update_a:
                    update_r = -1000
                    move["r"] = -1000
                    last_flap = False
                    high_death_flag = False
                    self.q_table[update_s][update_a] = (1 - self.lr) * (self.q_table[update_s][update_a]) + \
                                                self.lr * (update_r + self.gamma *
                                                                max(self.q_table[upadte_s_][0:2]))
                

            self.history_moves = []
       
        # 调整学习率 decay learning rate
        if self.lr > 0.1:
            self.lr = max(self.lr - self.lr_decay, 0.1)

        if len(self.q_table) == self.capacity:
            print('-------Q-table already have {} data-------'.format(self.capacity))
        
    
    def save_q_table(self, file_name):
        df = pd.DataFrame(self.q_table)
        df = df.T
        path = 'data/'+file_name+'.csv'
        df.to_csv(path)
        print('Saving Q-table to file: {}'.format(path))
    
    def load_q_table(self,file_path):
        df = pd.read_csv(file_path)
        for idx, data in df.iterrows():
            state = data[0]
            self.q_table[state] = [data['0'],data['1']]
        
        print('Loading Q-table from trained data: {}'.format(file_path))