const bool OK = 1
const bool ERR = 0

service ChatServer{
    // define chat interface

    /*
    使用python实现基于thrift的在线聊天功能(聊指的是服务端起来后，再起多个客户端，在客户端发消息，可以实现下述功能)
    1、聊天消息使用序列化后的数据传递，至少需要包含：消息发送方ip + 消息正文
    2、默认所有加入的人可一起聊天
    3、聊天可以请求加入群组，实现群聊天，非群组的人不能收到消息
    4、可选，只给群组里的某个人发消息
     */


     // regist
     string regist(1: string request)

     // login
     string login(1: string request)

     // deault group chat
     string chat_default_group(1:string request)

     // show default members
     string show_default_group_mem(1:string request)

     string show_groups(1:string request)

     // single chat
     string chat_with_single(1:string request)

     // create group
     string create_group(1:string request)

     // search group
     string search_group(1: string request)

     // add group
     string add_group(1:string request)

     // group chat of added
     string chat_group(1:string request)

     string show_group_mem(1:string request)

     // recv msgs, 如果是第三方queue，可以返回连接到该Queue的信息，然后让客户端去连接queue就好了，
     // 此处要是能直接返回queue就好了，我就会轻松很多
//     obj get_queue(1: string addr)
     string recv(1:string request)
}