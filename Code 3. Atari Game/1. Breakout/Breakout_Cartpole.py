import gym
import pylab
import random
import numpy as np
from gym import wrappers
from collections import deque
from keras.layers import Dense, Reshape, Flatten
from keras.optimizers import Adam
from keras.models import Sequential
from keras.layers.convolutional import Conv2D

EPISODES = 5000


class DQNAgent:
    def __init__(self, state_size, action_size):
        self.render = "False"

        self.state_size = state_size
        self.action_size = action_size

        self.epsilon = 1.0
        self.epsilon_start = 1.0
        self.epsilon_end = 0.1
        self.epsilon_decay = 1000000
        self.epsilon_decay_step = (self.epsilon_start - self.epsilon_end) / self.epsilon_decay

        self.batch_size = 32
        self.train_start = 50000
        self.update_target_rate = 10000
        self.discount_factor = 0.99
        self.learning_rate = 0.00025
        self.memory = deque(maxlen=1000000)

        self.model = self.build_model()
        self.target_model = self.build_model()
        self.update_target_model()

    def build_model(self):
        model = Sequential()
        # model.add(Reshape((1, 84, 84, 4), input_shape=(self.state_size,)))
        model.add(Conv2D(32, (8, 8), activation='relu', strides=(4, 4),
                         kernel_initializer='glorot_uniform', input_shape=self.state_size))
        model.add(Conv2D(64, (4, 4), activation='relu', strides=(2, 2),
                         kernel_initializer='glorot_uniform'))
        model.add(Conv2D(64, (3, 3), activation='relu', strides=(1, 1),
                         kernel_initializer='glorot_uniform'))
        model.add(Flatten())
        model.add(Dense(512, activation='relu', kernel_initializer='glorot_uniform'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(lr=0.00025, beta_1=0.95, beta_2=0.95,
                                                 epsilon=0.01, clipnorm=1.))
        return model

    def update_target_model(self):
        self.target_model.set_weights(self.model.get_weights())

    def get_action(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        else:
            q_value = self.model.predict(state)
            return np.argmax(q_value[0])

    def replay_memory(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
        if self.epsilon > self.epsilon_end:
            self.epsilon -= self.epsilon_decay_step
            # print(len(self.memory))

    def train_replay(self):
        # if len(self.memory) < self.train_start:
        #    return
        batch_size = min(self.batch_size, len(self.memory))
        mini_batch = random.sample(self.memory, batch_size)

        update_input = np.zeros((batch_size, self.state_size))
        update_target = np.zeros((batch_size, self.action_size))

        for i in range(batch_size):
            state, action, reward, next_state, done = mini_batch[i]
            target = self.model.predict(state)[0]

            if done:
                target[action] = reward
            else:
                target[action] = reward + self.discount_factor * \
                                          np.amax(self.target_model.predict(next_state)[0])
            update_input[i] = state
            update_target[i] = target

        self.model.fit(update_input, update_target, batch_size=batch_size, epochs=1, verbose=0)

    def load_model(self, name):
        self.model.load_weights(name)

    def save_model(self, name):
        self.model.save_weights(name)


def pre_processing(state):
    pass


if __name__ == "__main__":
    env = gym.make('BreakoutDeterministic-v3')

    state_size = (84, 84, 4)
    action_size = env.action_space.n

    agent = DQNAgent(state_size, action_size)

    scores, episodes, global_step = [], [], 0

    for e in range(EPISODES):
        done = False
        score = 0
        state = env.reset()

        while not done:
            if agent.render == "True":
                env.render()
            global_step += 1
            action = env.action_space.sample()
            next_state, reward, done, info = env.step(action)
            # next_state = np.reshape(next_state, [1, state_size])

            agent.replay_memory(state, action, reward, next_state, done)
            # agent.train_replay()
            score += reward
            state = next_state

            # if global_step % agent.update_target_rate == 0
            #    agent.update_target_model()

            if done:
                env.reset()
                scores.append(score)
                episodes.append(e)
                print("episode:", e, "  score:", score, "  memory length:", len(agent.memory),
                      "  epsilon:", agent.epsilon)