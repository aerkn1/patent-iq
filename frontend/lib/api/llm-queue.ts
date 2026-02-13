
type Task<T> = () => Promise<T>;

interface QueueItem<T> {
    task: Task<T>;
    resolve: (value: T | PromiseLike<T>) => void;
    reject: (reason?: any) => void;
}

export class ConcurrencyQueue {
    private queue: QueueItem<any>[] = [];
    private activeCount = 0;
    private readonly concurrency: number;

    constructor(concurrency: number) {
        this.concurrency = concurrency;
    }

    enqueue<T>(task: Task<T>): Promise<T> {
        return new Promise<T>((resolve, reject) => {
            this.queue.push({ task, resolve, reject });
            this.process();
        });
    }

    private async process() {
        if (this.activeCount >= this.concurrency || this.queue.length === 0) {
            return;
        }

        const item = this.queue.shift();
        if (!item) return;

        this.activeCount++;

        try {
            const result = await item.task();
            item.resolve(result);
        } catch (error) {
            item.reject(error);
        } finally {
            this.activeCount--;
            this.process();
        }
    }
}

export const llmQueue = new ConcurrencyQueue(5);
