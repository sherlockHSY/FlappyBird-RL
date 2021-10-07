from typing_extensions import runtime
from flappy_bird_env import FlappyBird
from q_learning import QLearning

import time

# 将环境的observation转换为Q-learning的state
def get_state(obs):
    """
    Get current state of bird in environment.
    :param x: bird x
    :param y: bird y
    :param vel: bird y velocity
    :param pipe: pipe
    :return: current state (x0_y0_v_y1) where x0 and y0 are diff to pipe0 and y1 is diff to pipe1
    """
    if obs == 'terminal':
        return obs
    [x, y, vel, pipe, upperPipes] = obs
    # Get pipe coordinates
    pipe0, pipe1 = pipe[0], pipe[1]
    if x - pipe[0]["x"] >= 50:
        pipe0 = pipe[1]
        if len(pipe) > 2:
            pipe1 = pipe[2]

    x0 = pipe0["x"] - x
    y0 = pipe0["y"] - y
    if -50 < x0 <= 0:
        y1 = pipe1["y"] - y
    else:
        y1 = 0

    # Evaluate player position compared to pipe
    if x0 < -40:
        x0 = int(x0)
    elif x0 < 140:
        x0 = int(x0) - (int(x0) % 10)
    else:
        x0 = int(x0) - (int(x0) % 70)

    if -180 < y0 < 180:
        y0 = int(y0) - (int(y0) % 10)
    else:
        y0 = int(y0) - (int(y0) % 60)

    if -180 < y1 < 180:
        y1 = int(y1) - (int(y1) % 10)
    else:
        y1 = int(y1) - (int(y1) % 60)

    state = str(int(x0)) + "_" + str(int(y0)) + "_" + str(int(vel)) + "_" + str(int(y1))
    
    return state

if __name__ == '__main__':
    # 初始化环境
    env = FlappyBird()
    env.seed(1)

    agent = QLearning(action_space= env.action_space,
                    learning_rate=0.7,
                    reward_decay=0.95, 
                    e_greedy=0.9)

    # 加载已训练好的Q table
    agent.load_q_table('data/q_table_iter_20000.csv')

    MAX_EPISODES = 18000 # 迭代次数接近19000次时,分数超过10000分，接近20000次时，分数接近700000分

    RENDER = True # 训练的时候建议设为False Better set False while training

    t = time.time()

    for ep in range(MAX_EPISODES):
        obs = env.reset()
        s = get_state(obs)

        while True:
            if RENDER:
                env.render(turn_on_sound=True) # 可视化环境

            # 选择动作 choose action
            a = agent.choose_action(s)

            # 与环境交互 interact with env
            obs_, r, done = env.step(a)
            s_ = get_state(obs_)

            # 更新Q-table update Q-table 
            agent.learn(s, a, r, s_, done)
            
            # 更新状态 update state
            s = s_

            if done:
                print('episode {} , score: {} , max score: {}'.format(str(ep), env.get_score(), env.get_max_score()))    
                break
            
    
    run_time = (time.time() - t) / 3600
    print('It took {} hours in training {} episodes'.format(run_time, MAX_EPISODES))    
    # 保存Q table
    agent.save_q_table('q_table_iter_'+str(MAX_EPISODES))

    

