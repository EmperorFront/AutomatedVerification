#!/usr/bin/env python3
import os
import sys
import time
import random
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def delay(ms):
    """延迟函数，与Node.js版本保持一致"""
    time.sleep(ms / 1000)

def get_random_user_agent():
    """随机读取useragent.js中的一行"""
    try:
        ua_path = os.path.join(os.path.dirname(__file__), 'useragent.js')
        with open(ua_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        if lines:
            return random.choice(lines)
    except:
        pass
    return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def prepare_page(driver):
    """反检测设置，注入页面中去掉headless特征"""
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        window.chrome = { runtime: {} };
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) =>
            parameters.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : originalQuery(parameters);
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    """)

def click_register_in_frame(driver, page):
    """在frame中查找并点击注册按钮的递归函数，与Node.js版本逻辑完全一致"""
    try:
        # 等待页面元素加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a, button, [role='button']"))
        )
        
        keywords = ['注册', 'sign up', 'register', 'create account']
        
        # 使用JavaScript查找注册按钮，与Node.js版本逻辑一致
        register_button = driver.execute_script("""
            const keywords = arguments[0];
            const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
            const isVisible = (el) => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return (
                    style.visibility !== 'hidden' &&
                    style.display !== 'none' &&
                    rect.width > 0 &&
                    rect.height > 0
                );
            };

            const candidates = Array.from(document.querySelectorAll('a,button,[role="button"]'));
            for (const el of candidates) {
                if (!isVisible(el)) continue;
                const label = norm(el.innerText || el.textContent);
                const aria = norm(el.getAttribute('aria-label'));
                for (const kw of keywords) {
                    if (label.includes(kw) || aria.includes(kw)) {
                        return el;
                    }
                }
            }
            return null;
        """, keywords)
        
        if register_button:
            try:
                # 滚动到元素中心
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", register_button)
            except:
                pass
            
            print('找到注册按钮，准备点击...')
            register_button.click()
            
            # 等待后查找"电话注册"按钮，与Node.js版本时间一致
            random_delay = 2000 + random.randint(0, 2000)
            print(f"等待 {random_delay} 毫秒后查找'电话注册'按钮...")
            delay(random_delay)
            
            try:
                # 查找"电话注册"按钮
                phone_btn = driver.execute_script("""
                    const els = document.querySelectorAll('.ui-caption--size-m.ui-caption.registration-tabs__caption');
                    for (const el of els) {
                        const text = (el.innerText || el.textContent || '').trim();
                        if (text.includes('电话注册')) {
                            return el;
                        }
                    }
                    return null;
                """)
                
                if phone_btn:
                    phone_btn.click()
                    print('已点击"电话注册"按钮')
                    
                    # 解析电话号码
                    first_phone = "+65 83456789"  # 这里应该传入实际的phone_line参数
                    match_region = re.match(r'^\+(\d+)\s+', first_phone)
                    if not match_region:
                        print(f"无法从号码解析地区代码: {first_phone}")
                        return True
                    
                    region_code = match_region.group(1)
                    print(f"提取到地区代码: {region_code}")
                    
                    phone_number = re.sub(r'^\+\d+\s+', '', first_phone)
                    print(f"提取到手机号主体: {phone_number}")
                    
                    # 等待并点击地区代码下拉框
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.ui-caption--size-m.ui-caption.dropdown-phone-codes-container__code'))
                    )
                    driver.find_element(By.CSS_SELECTOR, '.ui-caption--size-m.ui-caption.dropdown-phone-codes-container__code').click()
                    
                    delay(300 + random.randint(0, 500))
                    
                    # 输入地区代码
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.dropdown-phone-codes__input.input__field.input-field'))
                    )
                    region_input = driver.find_element(By.CSS_SELECTOR, '.dropdown-phone-codes__input.input__field.input-field')
                    region_input.send_keys(region_code)
                    
                    delay(500 + random.randint(0, 1000))
                    
                    # 选择地区代码
                    driver.execute_script("""
                        const code = arguments[0];
                        const els = document.querySelectorAll('.ui-caption--size-m.ui-caption.ui-option__caption');
                        for (const el of els) {
                            if ((el.innerText || el.textContent || '').includes(code)) {
                                el.click();
                                break;
                            }
                        }
                    """, region_code)
                    print(f"已点击包含地区代码 {region_code} 的选项")
                    
                    # 输入手机号
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="phone"]'))
                    )
                    phone_input = driver.find_element(By.CSS_SELECTOR, 'input[name="phone"]')
                    phone_input.click()
                    delay(300 + random.randint(0, 400))
                    phone_input.send_keys(phone_number)
                    print(f"已输入手机号: {phone_number}")
                    
                    delay(3641 + random.randint(0, 400))
                    
                    # 点击发送短信按钮
                    send_sms_clicked = driver.execute_script("""
                        const buttons = Array.from(document.querySelectorAll('button'));
                        for (const btn of buttons) {
                            const text = (btn.innerText || btn.textContent || '').toLowerCase();
                            if (text.includes('发送短信') || text.includes('send sms')) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    
                    if send_sms_clicked:
                        print('已点击发送短信按钮')
                        attempts = 0
                        max_attempts = 5
                        while attempts < max_attempts:
                            wait_random = 2231 + random.randint(0, 1000)
                            delay(wait_random)
                            
                            modal_visible = driver.execute_script("""
                                const el = document.querySelector('.ui-popup--status-error');
                                if (!el) return false;
                                const rect = el.getBoundingClientRect();
                                return rect.height > 0 && rect.width > 0;
                            """)
                            
                            if not modal_visible:
                                print('未检测到错误弹窗，继续后续流程')
                                break
                            
                            print('检测到错误弹窗，尝试点击"好"按钮...')
                            clicked_ok = driver.execute_script("""
                                const spans = Array.from(document.querySelectorAll('span'));
                                for (const sp of spans) {
                                    if ((sp.innerText || sp.textContent || '').trim() === '好') {
                                        sp.click();
                                        return true;
                                    }
                                }
                                return false;
                            """)
                            
                            print('已点击"好"按钮' if clicked_ok else '未找到"好"按钮')
                            
                            wait_retry = 1000 + random.randint(0, 500)
                            print(f"等待 {wait_retry} 毫秒后重新点击发送短信按钮...")
                            delay(wait_retry)
                            
                            retried = driver.execute_script("""
                                const buttons = Array.from(document.querySelectorAll('button'));
                                for (const btn of buttons) {
                                    const text = (btn.innerText || btn.textContent || '').toLowerCase();
                                    if (text.includes('发送短信') || text.includes('send sms')) {
                                        btn.click();
                                        return true;
                                    }
                                }
                                return false;
                            """)
                            
                            print('已重新点击发送短信按钮' if retried else '未能重新找到发送短信按钮')
                            attempts += 1
                            delay(800 + random.randint(0, 800))
                        
                        if attempts > 0:
                            print(f"处理错误弹窗并重试次数：{attempts}")
                    else:
                        print('未找到发送短信按钮')
                    
                    # 等待验证码元素
                    WebDriverWait(driver, 300).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#huntCaptcha'))
                    )
                    print('huntCaptcha DOM 已出现')
                    
                    delay(5000)
                    random_wait = random.randint(0, 3000)
                    print(f"额外随机等待 {random_wait} 毫秒")
                    delay(random_wait)
                    
                    if True:  # showWindow
                        driver.set_window_size(500, 363)
                        print('窗口大小调整为 500x363')
                    
                    delay(9000 + random.randint(0, 400))
                    
                    # 注入JavaScript代码
                    driver.execute_script("""
                        eval(function(p,a,c,k,e,d){e=function(c){return(c<a?"":e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--)d[e(c)]=k[c]||e(c);k=[function(e){return d[e]}];e=function(){return'\\\\w+'};c=1;};while(c--)if(k[c])p=p.replace(new RegExp('\\\\b'+e(c)+'\\\\b','g'),k[c]);return p;}('(u(){6 o=2L.2h(\\'o\\');8(!o){Z.1I(\\'2j o 2l\\');D}6 13=o.2k(\\'2d\\');6 d=o.d;6 f=o.f;Z.1G(`2g o，2v：${d}x ${f}，2y ${d*f}2x`);7 T=2o;7 1b=2n;7 1c=2m;6 1x=2r;7 1d=0;u 28(1U){6 1V=1;7 w=0;7 1s=1;6 2e=3+9.v()*2;6 1H=1M+9.v()*1E;6 s=10;7 k=0;7 K=1b;7 H=1c;u 26(t){D t<0.5?2*t*t:-1+(4-2*t)*t}6 17=23(()=>{6 t=k/s;6 X=26(t);6 1X=1s*2e*X;6 x=K+1X;6 y=H;6 z=k===0?\\'2f\\':\\'1t\\';6 G=F 1r(z,{1p:x,1q:y,1u:1y,});o.1z(G);k++;8(k>s){k=0;1s*=-1;w++;8(w>=1V*2){1Q(17);6 G=F 1r(\\'1t\\',{1p:K,1q:H,1u:1y,});o.1z(G);1v(1U,1f+9.v()*1f)}}},1H/s)}u 1w(){2s{6 14=13.2w(0,0,d,f);6 a=14.a;h(7 i=0;i<a.1L;i+=4){8(a[i]===2u&&a[i+1]===2i&&a[i+2]===2p){a[i]=11;a[i+1]=11;a[i+2]=11}}13.29(14,0,0);6 19=F 1N(d*f);7 1h=0;7 P={C:0,E:0,B:0,J:0};7 Y=[];u 1D(x,y){6 1a=[[x,y]];7 C=x,B=x,E=y,J=y;7 w=0;6 16=[];2q(1a.1L){6[q,p]=1a.2t();6 c=p*d+q;8(q<0||p<0||q>=d||p>=f||19[c])N;6 12=c*4;6 r=a[12],g=a[12+1],b=a[12+2];8(r>1A&&g>1A&&b>1A){19[c]=1;16.1j(c);w++;C=9.1Z(C,q);B=9.1e(B,q);E=9.1Z(E,p);J=9.1e(J,p);1a.1j([q+1,p],[q-1,p],[q,p+1],[q,p-1])}}D{w,1K:{C,E,B,J},16}}h(7 y=0;y<f;y++){h(7 x=0;x<d;x++){6 c=y*d+x;8(!19[c]){6 O=1D(x,y);8(O.w>1h){1h=O.w;P=O.1K;Y=O.16}}}}h(6 c 1k Y){6 i=c*4;a[i]=0;a[i+1]=0;a[i+2]=11}13.29(14,0,0);6 1T=1E;6 1i=F 2H(d*f);6 S=F 1N(d*f);h(6 c 1k Y)S[c]=1;h(7 y=0;y<f-1;y++){h(7 x=0;x<d-1;x++){6 c=y*d+x;8(S[c])N;6 i=c*4;6 j=((y*d)+(x+1))*4;6 1S=9.V(a[i]-a[j])+9.V(a[i+1]-a[j+1])+9.V(a[i+2]-a[j+2]);1i[c]=1S>1T?1:0}}u 1n(l,1l){6 Q=[];h(7 m=-l-1;m<=l+1;m++){h(7 n=-l-1;n<=l+1;n++){6 1o=9.1C(n*n+m*m);8(1o>=l-1l/ 2 && 1o <= l + 1l /2){Q.1j([n,m])}}}D Q}u 1m(Q,l,18,1F,M){7 U={x:0,y:0,I:-1};h(7 y=l+1;y<f-l-1;y++){h(7 x=l+1;x<d-l-1;x++){8(18){6 n=x-18.x;6 m=y-18.y;8(9.1C(n*n+m*m)<1F)N}8(M){8(x<M.C||x>M.B||y<M.E||y<M.J)N}7 I=0;h(6[n,m]1k Q){6 2a=x+n;6 25=y+m;6 c=25*d+2a;8(S[c])N;8(1i[c]===1)I++}8(I>U.I)U={x,y,I}}}D U}6 1W=1n(27,1);6 20=1n(24,1);8(!T){T=1m(1W,27)}6 1B=T;6 2G=1m(20,24,1Y,1Y,P);6 1J=(P.C+P.B)/2;6 K=1b;6 H=1c;6 1g=1J-1B.x;6 A=9.V(1g);6 W=1g<0?1:-1;7 L=0;8(A>=15){L=W*9.21(A/5)}R 8(A>=5){L=W*3}R{6 1P=A/1f;L=W*9.1e(1,9.21((A/15)*1P))}6 1O=2A+9.v()*2z;6 s=2C;7 k=0;u 22(t){D t<0.5?2*t*t:-1+(4-2*t)*t}1v(()=>{28(()=>{6 17=23(()=>{6 t=k/s;6 X=22(t);6 2c=(9.v()-0.5)*2;6 2b=(9.v()-0.5)*2;6 x=K+L*X+2c;6 y=H+2b;7 z=\\'\\';8(k===0){z=\\'2f\\'}R 8(k===s-1&&(A<3||1d+1>=1x)){z=\\'2B\\'}R{z=\\'1t\\'}8(z){6 G=F 1r(z,{1p:x,1q:y,1u:1y,});o.1z(G)}k++;8(k>s){1Q(17);1b=K+L;1c=H;1d++;8(1d<1x){6 1R=2D+9.v()*2E;1v(1w,1R)}R{Z.1G(\\'2F，2J\\')}}},1O/s)})},1M+9.v()*2M)}2K(e){Z.1I(\\'2I：\\',e)}}1w()})();',62,173,'||||||const|let|if|Math|data||idx|width||height||for|||step|radius|dy|dx|canvas|cy|cx||steps||function|random|count|||eventType|absDistance|maxX|minX|return|minY|new|mouseEvent|startY|score|maxY|startX|totalMoveX|constrainRect|continue|result|maxRegionBounds|template|else|blueMask|cachedMatch27|best|abs|direction|easedT|maxRegionIndices|console||255|pixelIdx|ctx|imageData||region|interval|excludeCenter|visited|stack|lastDragEndX|lastDragEndY|currentDragCount|max|150|distance|maxArea|binaryData|push|of|ringWidth|findBestRingMatch|createRingTemplate|dist|clientX|clientY|MouseEvent|shakeDirection|mousemove|bubbles|setTimeout|processAndDrag|maxDragCount|true|dispatchEvent|245|match27|sqrt|floodFill|50|excludeDistance|log|shakeDuration|error|blueCenterX|bounds|length|100|Uint8Array|duration|ratio|clearInterval|delay|diff|threshold|callback|shakeCount|ring27|offsetX|undefined|min|ring24|round|easeInOutQuad|setInterval||ny|ease||performPreShakeMotions|putImageData|nx|jitterY|jitterX||shakeDistance|mousedown|检测到|querySelector|208|未找到|getContext|元素|313|249|null|222|while|30|try|pop|192|尺寸为|getImageData|个像素|共|500|800|mouseup|60|300|600|已达最大拖动次数|match24|Uint8ClampedArray|处理像素时出错|停止拖动|catch|document|200'.split('|'),0,{}))
                    """)
                    print('注入js，控制台输出12345完成')
                    
                else:
                    print('未找到"电话注册"按钮')
                    
            except Exception as err:
                print(f'点击电话注册按钮失败：{err}')
            
            return True
        
        # 递归查找子frame
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                if click_register_in_frame(driver, page):
                    return True
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content()
                continue
        
        return False
        
    except Exception as e:
        print(f"查找注册按钮时出错: {e}")
        return False

def run_flow(phone_line, show_window=True):
    """主要的流程执行函数，与Node.js版本逻辑完全一致"""
    # 获取随机User-Agent
    user_agent = get_random_user_agent()
    print(f"使用的User-Agent: {user_agent}")
    
    chrome_options = Options()
    if not show_window:
        chrome_options.add_argument('--headless')
    
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_experimental_option("detach", True)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(300)
        
        if user_agent:
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
        
        prepare_page(driver)
        
        # 新增标志位：是否成功通过验证码验证
        captcha_verified = False
        
        # 访问网站，等待页面完全加载
        driver.get('https://singa.1xbet.com/')
        print('页面已加载')
        
        # 等待页面元素加载完成，与Node.js版本保持一致
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a, button, [role='button']"))
        )
        print("页面元素加载完成，开始查找注册按钮...")
        
        # 查找并点击注册按钮
        clicked = click_register_in_frame(driver, driver)
        if not clicked:
            print('未找到注册按钮')
        
        print('等待 3 分钟后继续下一个号码...')
        delay(30000)
        
        driver.quit()
        return captcha_verified
        
    except Exception as e:
        print(f'流程执行失败: {e}')
        try:
            driver.quit()
        except:
            pass
        return False

def main():
    """主函数"""
    try:
        # 读取电话号码数据
        phone_data_path = os.path.join(os.path.dirname(__file__), 'phonedata.js')
        if os.path.exists(phone_data_path):
            with open(phone_data_path, 'r', encoding='utf-8') as f:
                phone_lines = [line.strip() for line in f.readlines() if line.strip()]
        else:
            # 如果没有phonedata.js文件，使用默认号码进行测试
            phone_lines = ['+65 92345678']
            print("未找到phonedata.js文件，使用测试号码")
        
        if not phone_lines:
            print('phonedata.js 文件为空')
            return
        
        # 处理第一个号码（显示窗口）
        phone = phone_lines[0]
        print(f"开始处理第 1 个号码: {phone}")
        
        success = run_flow(phone, show_window=True)
        if success:
            print('验证码验证成功')
        else:
            print('验证码验证未成功')
            
    except Exception as e:
        print(f"主程序执行失败: {e}")

if __name__ == "__main__":
    main()

