/**
 * Utility type definitions
 */

/**
 * Readonly record type
 */
export type ReadonlyRecord<K extends string | number | symbol, V> = {
    readonly [P in K]: V;
};

/**
 * Partial recursive type
 */
export type DeepPartial<T> = {
    [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

/**
 * Required recursive type
 */
export type DeepRequired<T> = {
    [P in keyof T]-?: T[P] extends object ? DeepRequired<T[P]> : T[P];
};

/**
 * Promisify type
 */
export type Promisify<T> = Promise<T>;

/**
 * Nullable type
 */
export type Nullable<T> = T | null;

/**
 * Optional type
 */
export type Optional<T> = T | undefined;

/**
 * Value of object properties
 */
export type ValueOf<T> = T[keyof T];

/**
 * Constructor type
 */
export type Constructor<T> = new (...args: any[]) => T;

/**
 * Async function type
 */
export type AsyncFunction<T = void, Args extends any[] = any[]> = (
    ...args: Args
) => Promise<T>;

/**
 * Observer pattern type
 */
export interface Observer<T> {
    next: (value: T) => void;
    error: (error: any) => void;
    complete: () => void;
}
