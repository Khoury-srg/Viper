#[macro_use]
extern crate chrono;
extern crate dbcop;

#[macro_use]
extern crate serde;

use std::fs::File;

use dbcop::db::history::{Event, Session, Transaction};
use dbcop::verifier::Verifier;

use std::collections::HashMap;

use dbcop::consistency::Consistency;

pub type VarId = u64;
pub type Value = Vec<u8>;
pub type SetId = u64;
pub type SessionId = u64;
pub type TxnId = (SessionId, u64);
pub type OpId = (TxnId, u64);

#[derive(Debug, Clone, Deserialize)]
pub struct KVTransaction {
    t_id: TxnId,
    op: Vec<Event>,
    committed: bool,
}

use std::collections::HashSet;

fn main() {
    // let k = "Read(x1, 0), Write(x8, 300), Read(x4, 0), Read(x9, 0), Read(x7, 0)\n";
    // println!("{:?}", parse_transaction(k.as_bytes()).unwrap().1);

    // return;

    let filepath = "dumpfile.bin";
    let mut histories: Vec<Vec<Session>> = Vec::new();
    {
        let file = File::open(filepath).unwrap();
        let content: HashMap<SessionId, Vec<KVTransaction>> =
            serde_json::from_reader(file).unwrap();

        let mut history: Vec<Session> = Vec::new();

        for (s_id, session_deser) in content.iter() {
            let mut session = Vec::new();

            for txn_deser in session_deser {
                session.push(Transaction {
                    events: txn_deser.op.clone(),
                    success: txn_deser.committed,
                })
            }

            history.push(session);
        }

        histories.push(history);
    };

    // println!("number of sessions {}", histories[0].len());

    // for (i, v) in histories[0].iter().enumerate() {
    //     for (j, v) in v.iter().enumerate() {
    //         println!("{} {} {}", i, j, v.events.len());
    //     }
    // }

    // let mut count = 0;
    for (id, hist) in histories.iter().enumerate() {
        use std::path::PathBuf;
        let mut verifier = Verifier::new(PathBuf::from("solve_dir"));
        verifier.model("");

        let min_level = match verifier.verify(hist) {
            Some(Consistency::RepeatableRead) => Consistency::ReadCommitted,
            Some(Consistency::ReadAtomic) => Consistency::RepeatableRead,
            Some(Consistency::Causal) => Consistency::ReadAtomic,
            Some(Consistency::Prefix) => Consistency::Causal,
            Some(Consistency::SnapshotIsolation) => Consistency::Prefix,
            Some(Consistency::Serializable) => Consistency::SnapshotIsolation,
            None => Consistency::Serializable,
            _ => unreachable!(),
        };
        println!("{:?}", min_level);
    }
    // println!("bad histories {}/{}", count, histories.len());
}
