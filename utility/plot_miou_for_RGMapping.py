import basic_src.io_function as io_function
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

# wall_time_to_relative time
def wall_time_to_relative_time(wall_time_list):
    diff_hours = [(wall_time_list[idx+1] - wall_time_list[idx])/3600 for idx in range(len(wall_time_list) - 1)]
    mean_diff = sum(diff_hours)/len(diff_hours)

    relative_time = [0,mean_diff]
    acc_time = mean_diff
    for idx in range(len(diff_hours)):
        acc_time += diff_hours[idx]
        relative_time.append(acc_time)

    return min(relative_time), max(relative_time)


def plot_miou_step_time(miou_dict, save_path, type):

    fig = plt.figure(figsize=(6,4))
    ax1 = fig.add_subplot(111)

    ax1.plot(miou_dict['step'], miou_dict['class_0'], linestyle='-', color='tab:red', label="Background", linewidth=0.8)
    ax1.plot(miou_dict['step'], miou_dict['class_1'], linestyle='-', color='tab:blue', label="Rock glaciers", linewidth=0.8)
    ax1.plot(miou_dict['step'], miou_dict['overall'], 'k-.', label="Overall", linewidth=0.8)
    ax1.set_xlim([0, max(miou_dict['step'])])


    ax2 = ax1.twiny()    #have another x-axis for time
    min_t, max_t = wall_time_to_relative_time(miou_dict['wall_time'])
    ax2.set_xlim([min_t, max_t])
    ax2.set_xlabel("Training time (hours)", fontsize=10)

    ax1.grid(axis='y', ls='--', alpha=0.5, lw=0.4, color='grey')

    ax1.legend(fontsize=10, loc="lower right")  # loc="upper left"
    ax1.set_xlabel('Training iteration', fontsize=10)
    ax1.set_ylabel(type)
    ax1.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

    plt.tight_layout()  # adjust the layout, avoid cutoff some label to title
    plt.savefig(save_path, dpi=300)
    # plt.show()


file_path = '/Users/huyan/Data/WKL/automapping/WestKunlun_Sentinel2_2018_westKunlun_beta_exp14_Area30k/'
txt_path = file_path + 'westKunlun_beta_exp14_val_miou.txt'
type = 'Validation IoU'
save_path = '/Users/huyan/Data/WKL/Plots/' + type.replace(' ', '') + '.png'
dict_data = io_function.read_dict_from_txt_json(txt_path)
plot_miou_step_time(dict_data, save_path, type)