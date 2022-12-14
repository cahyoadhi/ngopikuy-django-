import json, time,datetime
from django.views import View
from django.utils import timezone
from django.contrib import messages
from ngopikuy.models import Order,Product
from django.shortcuts import render,redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from ngopikuy.controllers.decorators import  employee_only, admin_only
from django.http import StreamingHttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from ngopikuy.forms import ProductForm, OrderForm
from django.shortcuts import get_object_or_404
import itertools


class OrderDetail(View):
    def get(self, request, pk):
        order = Order.objects.get(tracking_no = pk)
        if order.status == "New-Order":
            Order.objects.filter(tracking_no = pk).update(status='Process')
        order_list = json.loads(order.list_order_json)['order_list']
        context = {'order':order, 'order_list':order_list}
        return render (request, 'page/employee/order_detail.html',context)

    
    def post(self, request, pk):
        order = Order.objects.get(tracking_no = pk)
        order.completed_times = datetime.datetime.now(tz=timezone.utc)
        order.save()
        Order.objects.filter(tracking_no = pk).update(status='Complete')
        messages.success(request, "Your order success")
        order_list = json.loads(order.list_order_json)['order_list']
        context = {'order':order, 'order_list':order_list}
        return render (request, 'page/employee/order_detail.html',context)


@login_required(login_url='login')
@employee_only
def DashBoardPage(request):
    employee_name = request.user
    group = Group.objects.get(user = employee_name)
    order = Order.objects.all()
    context = {'order': order,'name':employee_name,'group':group}
    return render (request, 'page/employee/dashboard.html',context)

def event_stream():
    initial_data = ""
    for i in itertools.count(start=1):
        data = json.dumps(list(Order.objects.values("id","user__username","tracking_no", "created_add", "status","payment","total_price").order_by('-status')), cls=DjangoJSONEncoder)
        if not initial_data == data:
            yield "\ndata: {}\n\n".format(data) 
            initial_data = data

class PostStreamView(View):
    def get(self, request):
        response = StreamingHttpResponse(event_stream(),status=200)
        response['Content-Type'] = 'text/event-stream'
        return response

@employee_only
def OrderListPage(request):
    order = Order.objects.all()
    if 'search' in request.GET:
        search = request.GET['search']
        query = Order.objects.filter(tracking_no__icontains=search)
        if query.exists():
            order = Order.objects.filter(tracking_no__icontains=search)
            print(order)
        else:
            order = 0
    context = {'order': order}
    return render (request, 'page/employee/order_list.html',context)

@employee_only
def ProductListPage(request):
    product = Product.objects.all()
    context = {'product': product}
    return render (request, 'page/employee/product_list.html',context)


@employee_only
def AddProduct(request):
    if request.method=='POST':
        form = ProductForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product Added!")
    form = ProductForm()
    return render(request, 'page/employee/add_product.html', {'form':form})

@employee_only
def EditProduct(request, pk):
    instance = get_object_or_404(Product, id=pk)
    form = ProductForm(instance=instance)
    if request.method=='POST':
        form = ProductForm(request.POST,request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Product edited!")

    return render(request, 'page/employee/edit_product.html', {'form':form, 'product':instance})

@admin_only
def DeleteProduct(request, pk):
    Product.objects.get(id=pk).delete()
    messages.success(request, 'Item Deleted')
    return redirect('productlist')

@employee_only
def EditOrder(request, pk):
    instance = get_object_or_404(Order, tracking_no=pk)
    form = OrderForm(instance=instance)
    if request.method=='POST':
        form = OrderForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Order edited!")

    return render(request, 'page/employee/edit_order.html', {'form':form, 'order':instance})    

@admin_only
def DeleteOrder(request, pk):
    Order.objects.get(tracking_no=pk).delete()
    messages.success(request, 'Order was Deleted')
    return redirect('orderlist')