import multiprocessing

class Processor:
    def __init__(self):
        pass

    def worker(self, procnum, return_dict, function, args):
        return_dict[procnum] = function(*args)

    def with_proc(self, function, *args):
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        jobs = []
        for i, f in enumerate(function):
            p = multiprocessing.Process(target=self.worker, args=(i, return_dict, f, args))
            jobs.append(p)
            print(f'starting job {i}')
            p.start()

        [proc.join() for proc in jobs]

        return return_dict

    def process_methodlist(self, methodlist, *args):
        x = self.with_proc(methodlist, *args)
        for k,v in x.items():
            methodlist[k] = v
        return methodlist


    def get_self(self):
        return self

