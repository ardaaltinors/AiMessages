from langchain.schema import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from prompts.message_analyze import system_prompt
from datetime import datetime
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")


class IsReplyNeeded(BaseModel):
    is_reply_needed: bool = Field(
        title="is_reply_needed",
    )


class LLMResponse(BaseModel):
    text: str = Field(title="text", description="Arda'nın cevabı")


def generate_reply(incoming_message) -> LLMResponse:
    # Chain 1: Determine if a reply is needed
    prompt_template1 = ChatPromptTemplate.from_messages([
        SystemMessage(content="""Gelen mesajı dikkatlice oku ve değerlendir:
        - Eğer mesajda soru, direkt bir istek veya cevap gerektirecek önemli bir ifade varsa, 'is_reply_needed' değeri True olmalıdır.
        - Eğer mesaj sadece bilgi veriyor, akışı sürdüren veya doğrudan cevap gerektirmeyen bir içerik barındırıyorsa, 'is_reply_needed' değeri False olmalıdır.
        Bu değerlendirmeyi yaparken, mesajın samimiyetini, bağlamını ve iletişimin akıcılığını göz önünde bulundurarak gerçek bir sohbet havası yakalaman gerekiyor.
        - Not: 'Sender: Me' ifadesi, mesajın kendimiz tarafından gönderildiğini gösterir. Yalnızca bu ifade varsa, cevap gerekmez.
        """),
        SystemMessage(content="Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        HumanMessage(content=incoming_message)
    ])
    
    chain1 = prompt_template1 | llm.with_structured_output(IsReplyNeeded)
    
    print("incoming_message:", incoming_message)
    
    try:
        is_reply = chain1.invoke({})
        print("IsReplyNeeded:", is_reply)
    except Exception as e:
        print("Error during is_reply_needed call:", e)
        return None

    # If no reply is needed, simply return without calling the second LLM
    if not is_reply.is_reply_needed:
        print("No reply needed for the incoming message.")
        return None

    # Chain 2: Generate the actual reply
    prompt_template2 = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        SystemMessage(content="Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        HumanMessage(content=incoming_message)
    ])
    
    chain2 = prompt_template2 | llm.with_structured_output(LLMResponse)
    
    try:
        response = chain2.invoke({})
        print("LLMResponse:", response)
    except Exception as e:
        print("Error during reply generation call:", e)
        return None
    
    return response


if __name__ == "__main__":
    incoming_message = "askim napion"
    response = generate_reply(incoming_message)
    print("Final response:", response)
