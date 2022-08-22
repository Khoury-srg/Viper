pub mod algo;
pub mod sat;
pub mod util;

#[derive(Debug, Clone, Copy, Ord, PartialOrd, Eq, PartialEq)]
pub enum Consistency {
    ReadCommitted,
    RepeatableRead,
    ReadAtomic,
    Causal,
    Prefix,
    SnapshotIsolation,
    Serializable,
    Inc,
}
