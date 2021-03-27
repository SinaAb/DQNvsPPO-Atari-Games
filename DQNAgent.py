import retro
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Activation, Dropout, Flatten, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import TensorBoard
from collections import deque
import numpy as np
import time

# Cusotm tensorboard class for log writing so we dont have 10 million logs haha
class ModifiedTensorBoard(TensorBoard):

    # Overriding init to set initial step and writer (we want one log file for all .fit() calls)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.step = 1
        self.writer = tf.summary.FileWriter(self.log_dir)

    # Overriding this method to stop creating default log writer
    def set_model(self, model):
        pass

    # Overrided, saves logs with our step number
    # (otherwise every .fit() will start writing from 0th step)
    def on_epoch_end(self, epoch, logs=None):
        self.update_stats(**logs)

    # Overrided
    # We train for one batch only, no need to save anything at epoch end
    def on_batch_end(self, batch, logs=None):
        pass

    # Overrided, so won't close writer
    def on_train_end(self, _):
        pass

    # Custom method for saving own metrics
    # Creates writer, writes custom metrics and closes writer
    def update_stats(self, **stats):
        self._write_logs(stats, self.step)


class DQNAgent:
    # initalize the DQN agent which trains a convultional model given pixel data of the game
    def __init__(self, env, replay_memory_size=50000, min_replay_memory_size=1000):
        self.env = env  # game environment
        self.model = self.create_model()  # the DQN network
        self.model_name = "DQN: " + self.env.gamename + "\nSize: " + str(self.env.observation_space.shape)

        # we freeze the weights of this model and use it for Q predicitions so that our graident descent is not
        # stochastic. We will then incrementaly update this model using the true model after some N training steps.
        self.target_model = self.create_model()
        self.target_model.set_weights(self.model.get_weights())  # copy the true model
        self.replay_memory_size = replay_memory_size  # total number of training steps to store
        self.min_replay_memory_size = min_replay_memory_size  # minimum number of steps to replay for model training
        self.replay_memory = deque(maxlen=self.replay_memory_size)  # create a queue for replay memory
        self.target_update_counter = 0  # counts number of training steps taken used to update the target model

        # our tensorboard for writing to one log for every time we call model.fit()
        #self.tensorboard = ModifiedTensorBoard(log_dir=f'logs/{self.model_name}-{int(time.time())}')

    # Creates a CNN with two CONV2D layers with ReLU, Pooling, and Dropout.
    # Data is finally passed through 2 Dense layers which outputs a softmax activated output of action probabilities
    def create_model(self):
        model = keras.Sequential()

        model.add(Conv2D(256, (3, 3), input_shape=self.env.observation_space.shape))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.2))

        model.add(Conv2D(256, (3, 3)))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.2))

        model.add(Flatten())  # this converts our 3D feature maps to 1D feature vectors
        model.add(Dense(64))

        model.add(Dense(self.env.action_space.n, activation='sigmoid'))
        model.compile(loss="mse", optimizer=Adam(lr=0.001), metrics=['accuracy'])

        return model

    def get_action_meanings(self):
        meaning = ""
        for i in range(self.env.action_space.n):
            act = np.zeros(self.env.action_space.n)
            act[i] = 1

            meaning += "Action: " + str(act) + " Meaning: " + str(self.env.get_action_meaning(act)) + "\n"

        return meaning

    def random_run(self):
        self.env.reset()
        while True:
            obs, rew, done, info = self.env.step(self.env.action_space.sample())
            self.env.render()
            if done:
                break
        self.env.close()

if __name__ == '__main__':
    env = retro.make(game='Airstriker-Genesis')
    print(env.observation_space)
    print(env.action_space)

    # agent = DQNAgent(env)
    # agent.random_run()